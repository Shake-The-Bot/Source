############
#
from __future__ import annotations
from Classes import ShakeBot, ShakeContext, ShakeEmbed, BadArgument
from discord import utils
from itertools import groupby
from re import Match
from Classes.i18n import _
from typing import Any, Dict, Optional, List, Iterable, Callable
from discord.ext.commands import CommandError, Command as _Command, Group, Cog as _Cog
from .menu import HelpFrontSource, Cog, Command, HelpMenu
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
        
        maybe_coro = utils.maybe_coroutine
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
        raise BadArgument(message="Unknown command/category. Use \"/help\" for help.", argument=string)


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