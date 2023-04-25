from __future__ import annotations
from logging import getLogger
from contextlib import suppress
from itertools import combinations as cmb, groupby
from copy import copy
from random import choice, sample
from re import Match

from discord.utils import format_dt, maybe_coroutine
from discord.ext.commands import CommandError, Command as _Command, Group, Cog as _Cog, Greedy, errors
from discord.ext import commands, menus

from Classes.pages import (
    ListPageSource, ItemPageSource, FrontPageSource, CategoricalMenu, 
    CategoricalSelect, Pages
)
from typing import (
    Literal, Union, Optional, get_args, get_origin, Any, Dict, 
    Optional, List, Iterable, Callable
)
from discord import (
    ButtonStyle, PartialEmoji, ui, NotFound, Forbidden, HTTPException, Attachment,
    Interaction, Guild, Member, User, TextChannel, Object, Message, VoiceChannel
)

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _, MISSING

########
#
class command():
    def __init__(self, ctx: ShakeContext, command: Optional[str], category: Optional[str]):
        self.bot = ctx.bot
        self.ctx = ctx
        self.command: str = command
        self.category: str = category
    

    async def __await__(self: command):
        cat_or_cmd = self.command or self.category

        if cat_or_cmd is None:
            await HelpPaginatedCommand(self.ctx).send_bot_help()
            return 
        
        if cat_or_cmd is not None and self.bot.get_cog(cat_or_cmd) is not None:
            await HelpPaginatedCommand(self.ctx).send_cog_help(self.bot.get_cog(cat_or_cmd))
            return 
        
        maybe_coro = maybe_coroutine
        keys = cat_or_cmd.split(' ')
        cmd = self.bot.all_commands.get(keys[0])
        help = HelpPaginatedCommand(ctx=self.ctx)
        if cmd is None:
            return help.command_not_found(keys[0])

        for key in keys[1:]:
            try: 
                found = cmd.all_commands.get(key)

            except AttributeError:
                kwargs = help.subcommand_not_found(cmd)
                await help.send_error_message(**kwargs)
                return

            else:
                if found is None:
                    kwargs = help.subcommand_not_found(cmd)
                    await help.send_error_message(**kwargs)
                    return

                cmd = found

        if isinstance(cmd, Group): 
            await help.send_group_help(cmd)
            return

        else: 
            await help.send_command_help(cmd)
            return

class HelpPaginatedCommand():
    ctx: ShakeContext

    def __init__(self: HelpPaginatedCommand, ctx: Optional[ShakeContext] = None):
        self.ctx = ctx

    async def on_help_command_error(self: HelpPaginatedCommand, ctx: ShakeContext, error: CommandError):
        self.ctx.bot.dispatch('command_error', ctx, error)
        return

    def command_not_found(self: HelpPaginatedCommand, string: str, /) -> ShakeEmbed:
        raise errors.BadArgument(message="Unknown command/category. Use \"/help\" for help.", argument=string)


    async def send_error_message(self: HelpPaginatedCommand, **kwargs) -> None:
        destination = self.get_destination()
        return await destination.send(**kwargs)


    async def filter_commands(self: HelpPaginatedCommand, commands: Iterable[_Command[Any, ..., Any]], /, *, sort: bool = False, key: Optional[Callable[[_Command[Any, ..., Any]], Any]] = None,) -> List[Command[Any, ..., Any]]:
        if sort and key is None:
            key = lambda c: c.name
        iterator = filter(lambda c: not c.hidden, commands)
        async def predicate(cmd: _Command[Any, ..., Any]) -> bool:
            try:
                return await cmd.can_run(self.ctx)
            except CommandError:
                return False
        ret = []
        for cmd in iterator:
            valid = await predicate(cmd)
            if valid:
                ret.append(cmd)
        if sort:
            ret.sort(key=key)
        return ret


    def subcommand_not_found(
        self: HelpPaginatedCommand, command: _Command[Any, ..., Any], string: str, /
    ) -> ShakeEmbed:
        embed = ShakeEmbed.default(self.ctx, )
        embed.set_author(
            name=f'Command "{command.qualified_name}" hat keine subcommands.',
            icon_url=self.ctx.bot.emojis.cross.url,
        )
        if isinstance(command, Group) and len(command.commands) > 0:
            embed.set_author(
                name=f'Command "{command.qualified_name}" hat keinen subcommand mit dem namen {string}',
                icon_url=self.ctx.bot.emojis.cross.url,
            )
        return {'embed': embed}


    def remove_mentions(self: HelpPaginatedCommand, string: str, /) -> str:
        def replace(
            obj: Match, *, transforms: Dict[str, str] = self.MENTION_TRANSFORMS
        ) -> str:
            return transforms.get(obj.group(0), "@invalid")

        return self.MENTION_PATTERN.sub(replace, string)


    def get_command_signature(self: HelpPaginatedCommand, command: _Command) -> str:
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = "|".join(command.aliases)
            fmt = f"[{command.name}|{aliases}]"
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}"


    async def all_commands(self: HelpPaginatedCommand, bot: ShakeBot, user):
        def key(command: _Command) -> str:
            cog = command.cog
            return '' if command.cog_name == 'help_extension' else cog.qualified_name

        filtered = []
        for command in bot.commands:
            if not hasattr(command.callback, 'extras'):
                filtered.append(command)
                continue
            if (await bot.is_owner(user) or not command.callback.extras.get('owner', False)) and (not command.callback.extras.get('hidden', False)):
                filtered.append(command)


        entries: list[_Command] = await self.filter_commands(
            filtered,
            sort=True, key=key,
        )
        all_commands: dict[_Cog, list[_Command]] = {}
        for name, children in groupby(entries, key=key):
            if name == '':  # "\U0010ffff"
                continue 
            cog = bot.get_cog(bot.get_cog(name).category())
            assert cog is not None
            all_commands.setdefault(cog, []).append(sorted(children, key=lambda c: c.qualified_name)[0])
        return all_commands


    async def send_bot_help(self: HelpPaginatedCommand):
        menu = HelpMenu(ctx=self.ctx, source=HelpFrontSource())
        commands = await self.all_commands(self.ctx.bot, self.ctx.author)
        menu.add_categories(commands)
        
        if await menu.setup():
            await menu.send()


    async def commands_from_cog(self: HelpPaginatedCommand, cog):
        def key(command) -> str:
            return command.cog.qualified_name if command.cog else "\U0010ffff"

        entries: list[_Command] = await self.filter_commands(
            self.ctx.bot.commands, sort=True, key=key
        )
        commands: list[_Command] = []
        for name, children in groupby(entries, key=key):
            if name == "\U0010ffff":
                continue
            category = self.ctx.bot.get_cog(self.ctx.bot.get_cog(name).category())
            assert category is not None
            if not cog == category:
                continue
            commands.append(sorted(children, key=lambda c: c.qualified_name)[0])
        return commands


    async def send_cog_help(self: HelpPaginatedCommand, cog):
        locale = await self.ctx.bot.locale.get_user_locale(self.ctx.author.id) or 'en-US'
        await self.ctx.bot.locale.set_user_locale(self.ctx.author.id, locale)
        if not getattr(cog, 'help_command_title', False):
            cog = self.ctx.bot.get_cog(cog.category())
        commands = await self.commands_from_cog(cog)
        source = Cog(self.ctx, cog, commands, prefix=self.ctx.clean_prefix, paginating=True)
        menu = HelpMenu(ctx=self.ctx, source=source, front=HelpFrontSource())
        menu.add_categories(await self.all_commands(self.ctx.bot, self.ctx.author))
        if setup := await menu.setup():
            await menu.send()


    async def send_command_help(self: HelpPaginatedCommand, command):
        locale = await self.ctx.bot.locale.get_user_locale(self.ctx.author.id) or 'en-US'
        await self.ctx.bot.locale.set_user_locale(self.ctx.author.id, locale)
        if command.name == "help":
            return await self.send_bot_help(self.ctx)
        category = self.ctx.bot.get_cog(command.cog.category())
        commands = await self.commands_from_cog(category)
        source = Cog(self.ctx, category, commands, paginating=True)
        menu = HelpMenu(ctx=self.ctx, source=source, front=HelpFrontSource())
        menu.add_categories(await self.all_commands(self.ctx.bot, self.ctx.author))
        if not await menu.setup():
            raise

        index = None
        items = {i: command for i, command in enumerate(commands)}
        for k, v in items.items():
            if v.qualified_name == command.qualified_name:
                index = k
                break
        source = Command()
        await menu.rebind(source, item=index)
        await menu.send()
#
############

logger = getLogger(__name__)
hear_to_tasks = dict()
def configurations(bot: ShakeBot):
    conf = {
        'beta': {
            'suffix': bot.emojis.help.beta, 
            'text': _('This command is new and is in its beta version')
        }, 
        'owner': {
            'suffix': bot.emojis.help.owner, 
            'text': _('Only the owner of the shake bot can run this command')
        },
        'premium': {
            'suffix': bot.emojis.help.shakeplus, 
            'text': _('Start a Shake+ subscription to run this command')
        }, 
        'permission': {
            'suffix': bot.emojis.help.permissions, 
            'text': _('This command requires certain rights from the user to be executed')
        },
    }
    return conf 
########
#
class HelpMenu(CategoricalMenu):
    def __init__(self, ctx: ShakeContext, source: menus.PageSource, front: Optional[FrontPageSource] = MISSING, **kwargs: Any):

        super().__init__(ctx, source=source, front=front, select=CategoricalSelect, selectsource=Cog, **kwargs)
        self.current_source = self.current_page = None

    async def hear(self):
        if not isinstance(self.source, ListPageSource): 
            return False
        commands = {i: command for i, command in enumerate(self.items)}
        hears_to = [command.qualified_name for command in commands.values()]
        def check(m): 
            return (m.author == self.ctx.author) and (m.clean_content in hears_to)
        try:  
            if self.ctx.author in hear_to_tasks: 
                hear_to_tasks[self.ctx.author].close()
            hear_to_tasks[self.ctx.author] = self.ctx.bot.wait_for('message', timeout=self.timeout, check=check)
            msg = await hear_to_tasks[self.ctx.author]
        except: 
            return
        else:
            index = None
            for k, v in commands.items():
                if v.qualified_name == msg.clean_content:
                    index = k
                    break
            if index is None:
                return await self.hear()
            await self.rebind(Command(), self.message, index)
            with suppress(NotFound, Forbidden, HTTPException): 
                await msg.delete()


    @ui.button(style=ButtonStyle.blurple, emoji='ℹ', row=2)
    async def go_to_info_page(self, interaction: Interaction, button: ui.Button): 
        is_frontpage = isinstance(self.source, FrontPageSource)
        
        if is_frontpage:
            assert self.current_source is not None and self.current_page is not None
            tmpsource, tmppage = (self.current_source, self.current_page)
            self.current_source = self.current_page = None
            await self.rebind(source=tmpsource, item=tmppage, interaction=interaction)
            return

        elif not is_frontpage:
            assert self.current_source is None and self.current_page is None
            self.current_source, self.current_page = (self.source, self.page)
            await self.rebind(source=HelpFrontSource(), item=2, interaction=interaction)
            return


    async def run_command(self, interaction: Interaction, command: commands.Command):
        if not interaction.response.is_done(): 
            await interaction.response.defer()
        msg = copy(self.ctx.message)
        msg.channel = self.ctx.channel
        msg.author = self.ctx.author
        msg.content = self.ctx.prefix + command.name
        new_ctx = await self.ctx.bot.get_context(msg, cls=type(self.ctx))
        await self.ctx.bot.invoke(new_ctx)


    def update(self, page: Optional[int] = None) -> None:
        super().update(page=page)
        is_frontpage = isinstance(self.source, FrontPageSource)
        self.go_to_info_page.style = (ButtonStyle.green if (self.current_source != None) else ButtonStyle.grey) if is_frontpage else ButtonStyle.blurple
        self.go_to_info_page.disabled = (False if (self.current_source != None) else True) if is_frontpage else False
        return


    async def show_page(self, interaction: Interaction, item: int) -> None:
        await super().show_page(interaction=interaction, item=item)
        await self.hear()


    def fill(self) -> None:
        super().fill()
        self.add_item(self.go_to_info_page)


def get_signature( self: commands.Command, menu: ui.View,):
    bot: ShakeBot = menu.ctx.bot
    ctx: ShakeContext = menu.ctx
    guild: Guild = menu.ctx.guild

    if self.usage is not None:
        return self.usage

    params = self.clean_params
    if not params:
        return {}, {}

    optionals = {}
    required = {}

    all_text_channel = {str(channel.name): channel.mention for channel in guild.text_channels}
    text_channel = (all_text_channel.get(sorted(list(all_text_channel.keys()), key=len, reverse=False)[0]) if bool(guild.text_channels) else None)
    
    all_members = {str(member.name): member.mention for member in guild.members}
    member = (all_members.get(sorted(list(all_members.keys()), key=len, reverse=False)[0]) if bool(guild.members) else None)

    all_voice_channel = {str(channel.name): channel.mention for channel in guild.voice_channels}
    voice_channel = (all_voice_channel.get(sorted(list(all_voice_channel.keys()), key=len, reverse=False)[0]) if bool(guild.voice_channels) else None)

    examples = {
        int: [choice(range(0, 100))],
        Member: [menu.ctx.bot.user.mention, menu.ctx.author.mention, member],
        User: [menu.ctx.bot.user.mention],
        TextChannel: [ctx.channel.mention if ctx.channel else None, text_channel],
        VoiceChannel: [voice_channel],
        Object: [guild.id],
        Message: [menu.ctx.message.id, menu.message.id if menu.message else None],
        str: ['abc', 'hello', 'xyz'],
        bool: ['True', 'False']
    }
    for name, param in params.items():
        greedy = isinstance(param.converter, Greedy)
        typin = get_origin(param.converter) == Union and get_args(param.converter)[-1] == type(None)
        optional = False  # postpone evaluation of if it's an optional argument

        if greedy:
            annotation = param.converter.converter
        elif typin:
            args = list(get_args(param.converter))
            del args[-1]
            annotation = choice(args)
        else:
            annotation = param.converter
        

        origin = getattr(annotation, '__origin__', None)
        example = choice(examples.get(annotation, [f'{{{name}}}'])) or f'{{{name}}}'

        if not greedy and origin is Union:
            none_cls = type(None)
            union_args = annotation.__args__
            optional = union_args[-1] is none_cls
            if len(union_args) == 2 and optional:
                annotation = union_args[0]
                origin = getattr(annotation, '__origin__', None)

        if annotation is Attachment:
            if optional:
                optionals[_("[{name} (upload a file)]".format(name=name))] = str(example)
            else:
                required[(_("<{name} (upload a file)>") if not greedy else _("[{name} (upload files)]…")).format(name=name)] = str(example)
            continue

        if origin is Literal:
            name = '|'.join(f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__)
            
        if not param.required:
            if param.displayed_default:
                optionals[f'[{name}: {annotation.__name__}]…' if greedy else f'[{name}: {annotation.__name__}]'] = str(example)
                continue
            else:
                optionals[f'[{name}: {annotation.__name__}]'] = str(example)
            continue

        elif param.kind == param.VAR_POSITIONAL:
            if self.require_var_positional:
                required[f'<{name}: {annotation.__name__}…>'] = str(example)
            else:
                optionals[f'[{name}: {annotation.__name__}…]'] = str(example)
        elif optional:
            optionals[f'[{name}: {annotation.__name__}]'] = str(example)
        else:
            if greedy:
                optionals[f'[{name}: {annotation.__name__}]…'] = str(example)
            else: 
                required[f'<{name}: {annotation.__name__}>'] = str(example) 
    
    return required, optionals


class Command(ItemPageSource):
    def format_page(self, menu: ui.View, item: int):
        command = {i: command for i, command in enumerate(menu.items)}[self.item]
        
        embed = ShakeEmbed.default(menu.ctx,
            title=_("{category} » {command} Command").format(category=menu.ctx.bot.get_cog(command.cog.category()).long_doc_title(), command=command.name.capitalize()), 
            description="{}".format(_(command.help).format(prefix=menu.ctx.prefix) if command.help else _("No more detailed description given."))
        )
        embed.set_author(name=_('More detailed command description'))
        required, optionals = get_signature(menu, command)
        if bool(required) or bool(optionals):
            count = 3 if len(optionals.items()) > 3 else len(optionals.items())+1
            combinations = [subset for L in range(len(optionals.keys()) + 1) for subset in cmb(optionals.keys(), L)]
            fetched = sample([combi for combi in combinations], count) # if not any(not bool(x) for x in combi)

            usgs = [[k for k in combina] for combina in fetched]
            exmpls = [[optionals[k] for k in combina] for combina in fetched]

            usage = [f'```\n{_("Usage of the {command} command").format(command=command.name.capitalize())}\n```']
            for usg in usgs:
                usage.append('\n> ' + '\n '.join([f'**/{command.name}** ' + ' '.join(required.keys()) + ' ' + ' '.join(usg)]))
            embed.add_field(name="\u200b", inline=False, value=''.join(usage))

            examples = [f'```\n{_("Examples of the {command} command").format(command=command.name.capitalize())}\n```']
            for exmpl in exmpls:
                examples.append('\n> ' + '\n '.join([f'**/{command.name}** ' + ' '.join(required.values()) + ' ' + ' '.join(exmpl)])) 
            embed.add_field(name="\u200b", inline=False, value=''.join(examples))

        bot_permissions = command.extras.get('permissions', {}).get('bot', [])
        user_permissions = command.extras.get('permissions', {}).get('user', [])
        if bool(bot_permissions) or bool(user_permissions):
            bot = []
            if bool(bot_permissions):
                for bot_permission in bot_permissions:
                    bot.append(f'{bot_permission}')
                bot = ', '.join(bot)
                bot = f'\n> **{_("Bot")}:**\n' + bot
            user = []
            if bool(user_permissions):
                for user_permission in user_permissions:
                    user.append(f'{user_permission}')
                user = ', '.join(user)
                user = f'\n> **{_("User")}:** ' + user
            embed.add_field(name="\u200b", inline=False, value=(
                f'```{_("Necessary user permissions")}```{user if bool(user) else str()}{bot if bool(bot) else str()}')
            )
            embed.add_field(name='\u200b', value=menu.ctx.bot.config.embed.footer, inline=False)
        return embed, None


class Cog(ListPageSource):
    def __init__(
            self, ctx: ShakeContext, 
            group: commands.Cog, items: list[commands.Command],
            paginating: bool = True, per_page: int = 6, **kwargs
        ):
        title: str = getattr(group, 'help_command_title', None) or f'{group.qualified_name} Befehle'
        super().__init__(
            ctx=ctx, group=group, items=items, description=group.description, 
            paginating=paginating, per_page=per_page, title=title
        )
        self.suffixes = set()

    def getsig(self, command: commands.Command):
        signature = []
        count = 28 + command.signature.count('…') + command.signature.count(' ') + command.signature.count('...')
        for argument in (command.signature if command.signature else '').replace('...', '…').split(' '):
            if not bool(argument):
                continue
            if len(''.join(signature)+argument)+1 > count:
                signature.append('[…]')
                break
            signature.append('{}'.format(argument))
        return signature

    def add_field(self, embed: ShakeEmbed, item: Any, config):
        suffix: dict[str, dict] = {
            extra: config[extra]
                for extra, key in getattr(item.callback, 'extras', {}).items() if key is True and extra in list(config.keys())
        }
        self.suffixes.update(set(suffix.keys()))
        arguments = (' `' + ' '.join(sig) + '`') if bool(sig := self.getsig(item)) else ''
        badges = (' **➜** '+' '.join([str(configuration['suffix']) for configuration in list(suffix.values())])) if bool(suffix) else ''
        emoji = getattr(item.cog, 'display_emoji', '👀')

        signature = f"> ` {self.items.index(item)+1}. ` {emoji} **➜** `/{item.qualified_name}`{arguments}" 
        embed.add_field(name=signature, inline=False, value='> '+(_(item.help).split('\n', 1)[0] if item.help else _("No help given... (You should report this)")).capitalize()+badges)
        return

    async def format_page(self, menu: Union[Pages, ui.View], items: list[commands.Command]):
        config = configurations(self.bot)
        menu.items = items
        locale = await self.bot.locale.get_user_locale(menu.ctx.author.id) or 'en-US'
        await self.bot.locale.set_user_locale(menu.ctx.author.id, locale)
        embed = ShakeEmbed.default(menu.ctx, title=self.title, description=self.description+"\n\u200b", )#discord.Colour(0xA8B9CD))
        embed.set_author(name=_("Page {current}/{max} ({entries} commands)").format(
            current=menu.page+1, max=self.get_max_pages(), entries=len(self.entries)
        ))
        for item in items:
            self.add_field(embed, item, config=config)            

        information = ["**{0}・{1}**".format(config[key].get('suffix'), config[key].get('text')) for key in self.suffixes]

        if bool(information): 
            information.append(_("Use \"/help <command>\" to get more detailed information "))
            embed.add_field(name="\u200b", value="\n".join(information))

        return embed, None


class HelpFrontSource(FrontPageSource):
    def __init__(self) -> None:
        super().__init__()
        self.timeouted = None

    def __call__(self, timeout: bool = False) -> Any:
        self.timeouted = timeout
        return self

    def is_paginating(self) -> bool: 
        return True

    def get_max_pages(self) -> Optional[int]: 
        return 3

    async def get_page(self, index: int) -> Any:
        self.index = index
        return self

    def format_page(self, menu: ui.View, items: Any):
        embed = ShakeEmbed.default(menu.ctx, title = (
            _("{emoji} Bot Help (Timeouted)") if self.timeouted else _("{emoji} Bot Help")).format(
                emoji=PartialEmoji(animated=True, name='thanks', id=984980175525666887
            )
        ))
        if self.index in [1, 2]:
            embed.description = _(
                """Hello and welcome to my help page {emoji}
                Type `{prefix}help <command/category>` to get more information on a\ncommand/category."""
            ).format(
                emoji='', 
                prefix=menu.ctx.clean_prefix
            )
            embed.add_field(
                name=_("Support Server"), inline=False,
                value=_("You can get more help if you join the official server at\n{support_server}").format(
                    support_server=menu.ctx.bot.config.other.server
                )
            )
        file = None
        if self.index == 0:
            embed.set_image(url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png")
            embed.add_field(name=_("Who am I?"), inline=False,
                value=_(
                    """{user}, which is partially intended for the public.
                    Written with only `{lines:,}` lines of code. Please be nice""").format(
                        user=menu.ctx.bot.user.mention, lines=menu.ctx.bot.lines
                    ))
        elif self.index == 1:
            embed.add_field(name=_("What am I for?"), inline=False,
                value=_(
                    """I am a functional all-in-one bot that will simplify setting up your server for you!

                    I have been created {created_at} & 
                    I have functions like voting, level system, music, moderation & much more. 
                    You can get more information by using the dropdown menu below.
                    dropdown menu.""").format(created_at=format_dt(menu.ctx.bot.user.created_at, "F")))
        elif self.index == 2:
            entries = (
                ('<' + _('argument') + '>', _("Stands for the argument being __**necessary**__.")),
                ('[' + _('argument') + ']', _("Stands for that the argument is __**optional**__.")),
                ('[A|B]', _("Stands for the argument can be __**either A or B**__.")),
                (f"[{_('argument')}]…", _(
                    """Stands for the fact that you can use multiple arguments.

                    Now that you know the basics, you should still know that...
                    __**You don't include the parentheses!**__"""
                ),
            ))
            embed.add_field(name=_("How do I use the bot?"), value=_("Reading the bot structure is pretty easy."))
            for name, value in entries: embed.add_field(name=name, value=value, inline=False)
        return embed, file
#
############