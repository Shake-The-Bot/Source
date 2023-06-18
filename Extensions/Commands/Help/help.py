from __future__ import annotations

from contextlib import suppress
from copy import copy
from itertools import chain
from itertools import combinations as cmb
from itertools import groupby
from random import sample
from typing import Any, Callable, Coroutine, Dict, Iterable, List, Optional

from discord import (
    ButtonStyle,
    Forbidden,
    HTTPException,
    Interaction,
    Message,
    NotFound,
    PartialEmoji,
    ui,
)
from discord.ext import commands, menus
from discord.ext.commands import Cog, Command, CommandError, Group, errors
from discord.utils import format_dt, maybe_coroutine

from Classes import (
    MISSING,
    Category,
    ShakeBot,
    ShakeCommand,
    ShakeContext,
    ShakeEmbed,
    TextFormat,
    _,
    get_signature,
)
from Classes.accessoires import (
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
    ShakePages,
)
from Classes.types import CATEGORYS, Categorys

########
#
hear_to_tasks = dict()

configurations: Callable[
    [ShakeBot], dict[str, dict[str, PartialEmoji | str]]
] = lambda bot: {
    "beta": {
        "suffix": bot.emojis.help.beta,
        "text": _("This command is new and is in its beta version"),
    },
    "owner": {
        "suffix": bot.emojis.help.owner,
        "text": _("Only the owner of the shake bot can run this command"),
    },
    "premium": {
        "suffix": bot.emojis.help.shakeplus,
        "text": _("Start a Shake+ subscription to run this command"),
    },
    "permissions": {
        "suffix": bot.emojis.help.permissions,
        "text": _("This command requires certain rights from the user to be executed"),
    },
}


class command(ShakeCommand):
    def __init__(self, ctx, command: Optional[str], category: Optional[Category]):
        super().__init__(ctx)
        self.command: str = command
        self.category: Optional[CATEGORYS] = category

    async def __await__(self: command):
        if self.category is not None:
            name: Categorys = Categorys[self.category.lower()].value
            self.category = self.ctx.bot.get_cog(name)

        cat_or_cmd = self.command or self.category

        if cat_or_cmd is None:
            await HelpPaginatedCommand(self.ctx).bot_help()
            return

        if isinstance(cat_or_cmd, Category):
            await HelpPaginatedCommand(self.ctx).cog_help(cat_or_cmd)
            return

        keys = cat_or_cmd.split(" ")
        cmd = self.bot.all_commands.get(keys[0])
        help = HelpPaginatedCommand(ctx=self.ctx)
        if cmd is None:
            return help.command_not_found(keys[0])

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)

            except AttributeError:
                kwargs = help.subcommand_not_found(cmd)
                return await self.ctx.chat(**kwargs)

            else:
                if found is None:
                    kwargs = help.subcommand_not_found(cmd)
                    return await self.ctx.chat(**kwargs)
                cmd = found

        if isinstance(cmd, Group):
            return await help.group_help(cmd)

        else:
            return await help.command_help(cmd)


class HelpPaginatedCommand:
    def __init__(self, ctx: Optional[ShakeContext] = None):
        self.ctx: ShakeContext = ctx

    async def on_help_command_error(self, ctx: ShakeContext, error: CommandError):
        return self.ctx.bot.dispatch("command_error", ctx, error)

    def command_not_found(self, string: str, /) -> ShakeEmbed:
        self.ctx.bot.dispatch(
            "command_error",
            self.ctx,
            errors.BadArgument(
                _('Unknown command `{argument}`. Use "/help" for help.').format(
                    argument=string
                )
            ),
        )

    async def filter_commands(
        self,
        commands: Iterable[Command[Any, ..., Any]],
        /,
        *,
        sort: bool = False,
        key: Optional[Callable[[Command[Any, ..., Any]], Any]] = None,
    ) -> List[Command[Any, ..., Any]]:
        if sort and key is None:
            key = lambda c: c.name
        iterator = filter(lambda c: not c.hidden, commands)

        async def predicate(cmd: Command[Any, ..., Any]) -> bool:
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
        self, command: Command[Any, ..., Any], string: str, /
    ) -> ShakeEmbed:
        embed = ShakeEmbed.default(
            self.ctx,
        )
        embed.set_author(
            name=f'Command "{command.qualified_name}" hat keine subcommands.',
            icon_url=self.ctx.bot.emojis.cross.url,
        )
        if isinstance(command, Group) and len(command.commands) > 0:
            embed.set_author(
                name=f'Command "{command.qualified_name}" hat keinen subcommand mit dem namen {string}',
                icon_url=self.ctx.bot.emojis.cross.url,
            )
        return {"embed": embed}

    async def commands(
        self,
        category: Optional[Cog] = None,
    ) -> Dict[Cog, list[Command]]:
        filtered = []
        for command in self.ctx.bot.commands:
            if not hasattr(command.callback, "extras"):
                filtered.append(command)
                continue
            if (
                await self.ctx.bot.is_owner(self.ctx.author)
                or not command.callback.extras.get("owner", False)
            ) and (not command.callback.extras.get("hidden", False)):
                filtered.append(command)

        entries: Dict[Cog, List[Command]] = groupby(
            await self.filter_commands(
                filtered,
                sort=True,
                key=lambda command: command.qualified_name,
            ),
            key=lambda command: None
            if command.cog.__class__.__name__ == "help_extension"
            else command.cog,
        )

        wanted: dict[Cog, list[Command]] = dict()
        for cog, commands in entries:
            if not bool(cog):
                continue

            cogs_category = self.ctx.bot.get_cog(cog.__class__.__bases__[0].__name__)
            assert not cogs_category is None

            if category:
                if not cogs_category == category:
                    continue

            wanted.setdefault(cogs_category, []).append(
                sorted(commands, key=lambda c: c.qualified_name)[0]
            )
        return wanted

    async def bot_help(self):
        menu = HelpMenu(ctx=self.ctx, source=Front(), help=self)
        commands: Dict[Cog, list[Command]] = await self.commands()
        menu.add_categories(categories=commands)

        if not await menu.setup():
            raise
        await menu.send(ephemeral=True)

    async def cog_help(self, cog):
        locale = (
            await self.ctx.bot.locale.get_user_locale(self.ctx.author.id) or "en-US"
        )
        await self.ctx.bot.locale.set_user_locale(self.ctx.author.id, locale)

        commands = await self.commands()

        source = CategorySource(
            self.ctx,
            group=cog,
            items=commands.get(cog, []),
            prefix=self.ctx.clean_prefix,
            paginating=True,
        )
        menu = HelpMenu(ctx=self.ctx, source=source, front=Front(), help=self)

        menu.add_categories(categories=commands)
        if not await menu.setup():
            raise
        await menu.send(ephemeral=True)

    async def group_help(self, command: Command):
        if command.name == "help":
            return await self.bot_help()

        source = GroupPage(self.ctx, group=command)
        menu = HelpMenu(ctx=self.ctx, source=source, front=Front(), help=self)

        all_commands: Dict[Cog, List[Command]] = await self.commands()
        menu.add_categories(categories=all_commands)

        if not await menu.setup():
            raise

        await menu.send(ephemeral=True)

    async def command_help(self, command: Command):
        if command.name == "help":
            return await self.bot_help()

        source = CommandSource(self.ctx, item=command)
        menu = HelpMenu(ctx=self.ctx, source=source, front=Front(), help=self)

        all_commands: Dict[Cog, List[Command]] = await self.commands()
        menu.add_categories(categories=all_commands)

        if not await menu.setup():
            raise

        await menu.send(ephemeral=True)


class HelpSelect(CategoricalSelect):
    view: HelpMenu

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        assert self.categories is not None
        value = self.values[0]
        if value == "ShakeBack":
            if isinstance(self.view.source, FrontPageSource):
                if self.view.page == 0:
                    await interaction.response.defer()
                    await maybe_coroutine(self.view.on_stop, interaction=interaction)
                else:
                    await self.view.rebind(
                        self.view.front(), 0, interaction=interaction
                    )
            else:
                if isinstance(self.view.source, CommandSource):
                    category = self.view.source.category
                    help: HelpPaginatedCommand = self.help
                    commands = await help.commands(category=category)
                    source = CategorySource(
                        ctx=self.view.ctx,
                        group=category,
                        items=list(chain(*commands.values())),
                    )
                    page = source.get_page_from_item(item=self.view.source.item)
                    await self.view.rebind(
                        source=source,
                        page=page,
                        interaction=interaction,
                    )
                elif isinstance(self.view.source, CategorySource):
                    await self.view.rebind(self.view.front(), interaction=interaction)
                else:
                    await self.view.rebind(
                        self.view.front(), 0, interaction=interaction
                    )
        else:
            group = self.find.get(value, MISSING)
            items = self.categories.get(group, MISSING)

            if any(_ is MISSING for _ in (group, items)):
                await interaction.response.send_message(
                    _("This category either does not exist or has no items for you."),
                    ephemeral=True,
                )
                return

            source = self.source(
                ctx=self.ctx, group=group, items=items, interaction=interaction
            )
            self.view.cache["source"] = self.view.cache["page"] = None
            await self.view.rebind(source, interaction=interaction)


class HelpMenu(CategoricalMenu):
    help: HelpPaginatedCommand

    def __init__(
        self,
        ctx: ShakeContext,
        source: menus.PageSource,
        help: HelpPaginatedCommand,
        front: Optional[FrontPageSource] = MISSING,
        **kwargs: Any,
    ):
        super().__init__(
            ctx,
            source=source,
            front=front,
            select=HelpSelect(ctx, source=CategorySource, help=help),
            **kwargs,
        )
        self.cache["source"] = self.cache["page"] = None

    async def hear(self):
        if not isinstance(self.source, CategorySource):
            return False

        all_commands = {command.name: command for command in self.source.items} | {
            str(i): command for i, command in enumerate(self.source.items, 1)
        }

        def check(m: Message):
            return (m.author == self.ctx.author) and (
                m.clean_content in list(all_commands.keys())
            )

        try:
            if self.ctx.author in hear_to_tasks:
                hear_to_tasks[self.ctx.author].close()
            hear_to_tasks[self.ctx.author] = self.ctx.bot.wait_for(
                "message", timeout=self.timeout, check=check
            )
            msg: Message = await hear_to_tasks[self.ctx.author]
        except:
            return
        else:
            command = all_commands[msg.clean_content]
            if command is None:
                return await self.hear()

            if isinstance(command, Group):
                source = GroupPage(self.ctx, group=command)
            else:
                source = CommandSource(self.ctx, item=command)
            await self.rebind(source)
            with suppress(NotFound, Forbidden, HTTPException):
                await msg.delete()

    @ui.button(style=ButtonStyle.blurple, emoji="ℹ", row=2)
    async def go_to_info_page(self, interaction: Interaction, button: ui.Button):
        is_frontpage = isinstance(self.source, FrontPageSource)

        if is_frontpage:
            assert (
                self.cache.get("source", MISSING) != MISSING
                and self.cache.get("page", MISSING) != MISSING
            )
            tmpsource, tmppage = (self.cache["source"], self.cache["page"])
            self.cache["source"] = self.cache["page"] = None
            await self.rebind(tmpsource, tmppage, interaction=interaction)
            return

        elif not is_frontpage:
            assert (
                self.cache.get("source", MISSING) == None
                and self.cache.get("page", MISSING) == None
            )
            self.cache["source"], self.cache["page"] = (self.source, self.page)
            await self.rebind(Front(), 2, interaction=interaction)
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
        self.go_to_info_page.style = (
            (ButtonStyle.green if (self.cache["source"] != None) else ButtonStyle.grey)
            if is_frontpage
            else ButtonStyle.blurple
        )
        self.go_to_info_page.disabled = (
            (False if (self.cache["source"] != None) else True)
            if is_frontpage
            else False
        )
        return

    async def show_page(self, interaction: Interaction, item: int) -> None:
        await super().show_page(interaction=interaction, item=item)
        await self.hear()
        return

    async def rebind(
        self,
        source: menus.PageSource,
        page: Optional[int] = 0,
        interaction: Optional[Interaction] = None,
        update: Optional[bool] = True,
    ) -> None:
        await super().rebind(source, page, interaction, update)
        await self.hear()
        return

    def fill(self) -> None:
        super().fill()
        self.add_item(self.go_to_info_page)


class CategorySource(ListPageSource):
    group: Category

    def __init__(
        self,
        ctx: ShakeContext,
        group: Category,
        items: list[commands.Command],
        paginating: bool = True,
        per_page: int = 6,
        **kwargs: Any,
    ):
        title: str = getattr(group, "title", MISSING)
        assert not title is MISSING

        super().__init__(
            ctx=ctx,
            group=group,
            items=items,
            description=group.description,
            paginating=paginating,
            per_page=per_page,
            title=title,
        )
        self.suffixes = set()

    def get_page_from_item(self, item: Command) -> int:
        index = self.items.index(item)

        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1

        for page in range(pages):
            visual = page + 1
            indexes = range(page * self.per_page, visual * self.per_page)
            if index in indexes:
                return page

    def signature(self, command: commands.Command):
        signature = []
        count = (
            28
            + command.signature.count("…")
            + command.signature.count(" ")
            + command.signature.count("...")
        )
        for argument in (
            getattr(command, "signature", "").replace("...", "…").split(" ")
        ):
            if not bool(argument):
                continue
            if len("".join(signature) + argument) + 1 > count:
                signature.append("[…]")
                break
            signature.append("{}".format(argument))
        return signature

    def add_field(self, embed: ShakeEmbed, item: Command, config):
        suffix: dict[str, dict] = {
            extra: config[extra]
            for extra, key in getattr(item.callback, "extras", {}).items()
            if key is True and extra in set(config.keys())
        }
        self.suffixes.update(set(suffix.keys()))
        arguments = (
            (" `" + " ".join(sig) + "`") if bool(sig := self.signature(item)) else ""
        )
        badges = (
            (
                " **➜** "
                + " ".join(
                    [str(configuration["suffix"]) for configuration in suffix.values()]
                )
            )
            if bool(suffix)
            else ""
        )
        emoji = getattr(item.cog, "display_emoji", "👀")

        signature = f"> ` {self.items.index(item)+1}. ` {emoji} **➜** `/{item.qualified_name}`{arguments}"
        info = (
            " " + _("(has also more sub-commands)") if isinstance(item, Group) else ""
        )
        help = (
            _(item.help).split("\n", 1)[0]
            if item.help
            else _("No help given... (You should report this)")
        )

        embed.add_field(
            name=signature + info,
            inline=False,
            value=TextFormat.blockquotes(help).capitalize() + badges,
        )
        return

    async def format_page(
        self, menu: ShakePages | ui.View, items: list[commands.Command]
    ):
        config = configurations(self.bot)
        menu.items = items
        locale = await self.bot.locale.get_user_locale(menu.ctx.author.id) or "en-US"
        await self.bot.locale.set_user_locale(menu.ctx.author.id, locale)
        embed = ShakeEmbed.default(
            menu.ctx,
            title=self.group.title,
            description=self.group.description + "\n\u200b",
        )  # discord.Colour(0xA8B9CD))
        embed.set_author(
            name=_("Page {current}/{max} ({entries} commands)").format(
                current=menu.page + 1,
                max=self.get_max_pages(),
                entries=len(self.entries),
            )
        )
        for item in items:
            self.add_field(embed, item, config=config)

        last_embed = [
            "**{0}・{1}**".format(config[key].get("suffix"), config[key].get("text"))
            for key in self.suffixes
        ]
        if bool(last_embed):
            embed.add_field(name="\u200b", value="\n".join(last_embed))
        else:
            embed.advertise(self.bot)

        return embed, None


class CommandSource(ItemPageSource):
    command: Command

    async def get_page(self, page: Command) -> Coroutine[Any, Any, Any]:
        self.page: Command = page
        return self

    def format_page(self, menu: ShakePages, items: Any, **kwargs: Any):
        self.cog: Cog = self.item.cog
        self.category = menu.bot.get_cog(self.cog.__class__.__bases__[0].__name__)
        embed = ShakeEmbed.default(
            menu.ctx,
            title=_("{category} » {command} Command").format(
                category=self.category.label,
                command=self.item.name.capitalize(),
            ),
            description="{}".format(
                _(self.item.help).format(prefix=menu.ctx.prefix)
                if self.item.help
                else _("No more detailed description given.")
            ),
        )
        embed.set_author(name=_("More detailed command description"))
        required, optionals = get_signature(menu, self.item)
        if bool(required) or bool(optionals):
            count = 3 if len(optionals.items()) > 3 else len(optionals.items()) + 1
            combinations = [
                subset
                for L in range(len(optionals.keys()) + 1)
                for subset in cmb(optionals.keys(), L)
            ]
            fetched = sample(
                [combi for combi in combinations], count
            )  # if not any(not bool(x) for x in combi)

            usgs = [[k for k in combina] for combina in fetched]
            exmpls = [[optionals[k] for k in combina] for combina in fetched]

            usage = [
                f'```\n{_("Usage of the {command} command").format(command=self.item.name.capitalize())}\n```'
            ]
            for usg in usgs:
                usage.append(
                    "\n> "
                    + "\n ".join(
                        [
                            f"**/{self.item.name}** "
                            + " ".join(required.keys())
                            + " "
                            + " ".join(usg)
                        ]
                    )
                )
            embed.add_field(name="\u200b", inline=False, value="".join(usage))

            examples = [
                f'```\n{_("Examples of the {command} command").format(command=self.item.name.capitalize())}\n```'
            ]
            for exmpl in exmpls:
                examples.append(
                    "\n> "
                    + "\n ".join(
                        [
                            f"**/{self.item.name}** "
                            + " ".join(required.values())
                            + " "
                            + " ".join(exmpl)
                        ]
                    )
                )
            embed.add_field(name="\u200b", inline=False, value="".join(examples))

        bot = self.item.extras.get("permissions", {}).get("bot", [])
        user = self.item.extras.get("permissions", {}).get("user", [])

        if any([bool(user), bool(bot)]):
            embed.add_field(
                name="\u200b",
                inline=False,
                value=TextFormat.multicodeblock(
                    "{}\n{}\n{}\n{}".format(
                        _("Necessary user permissions"),
                        ", ".join([str(_) for _ in user]),
                        _("Necessary bot permissions"),
                        ", ".join([str(_) for _ in bot]),
                    )
                ),
            )

        embed.advertise(self.bot)
        return embed, None


class GroupPage(ListPageSource):
    def __init__(
        self,
        ctx: ShakeContext,
        group: Group,
        paginating: bool = True,
        per_page: int = 3,
        **kwargs: Any,
    ):
        title: str = _("Commands of the {group} group").format(group=group.name)

        super().__init__(
            ctx=ctx,
            group=group,
            items=list(group.commands),
            description="{}".format(
                _(group.help).format(prefix=ctx.prefix)
                if group.help
                else _("No more detailed description given.")
            ),
            paginating=paginating,
            per_page=per_page,
            title=title,
        )
        self.suffixes = set()

    def getsig(self, command: commands.Command):
        signature = []
        count = (
            28
            + command.signature.count("…")
            + command.signature.count(" ")
            + command.signature.count("...")
        )
        for argument in (
            getattr(command, "signature", "").replace("...", "…").split(" ")
        ):
            if not bool(argument):
                continue
            if len("".join(signature) + argument) + 1 > count:
                signature.append("[…]")
                break
            signature.append("{}".format(argument))
        return signature

    def add_field(self, embed: ShakeEmbed, item: Command, config: configurations):
        suffix: dict[str, dict] = {
            extra: config[extra]
            for extra, key in getattr(item.callback, "extras", {}).items()
            if key is True and extra in set(config.keys())
        }
        self.suffixes.update(set(suffix.keys()))
        arguments = (
            (" `" + " ".join(sig) + "`") if bool(sig := self.getsig(item)) else ""
        )
        badges = (
            (
                " **➜** "
                + " ".join(
                    [str(configuration["suffix"]) for configuration in suffix.values()]
                )
            )
            if bool(suffix)
            else ""
        )
        emoji = getattr(item.cog, "display_emoji", "👀")

        signature = f"> ` {self.items.index(item)+1}. ` {emoji} **➜** `/{item.qualified_name}`{arguments}"
        embed.add_field(
            name=signature,
            inline=False,
            value="> "
            + (
                _(item.help).split("\n", 1)[0]
                if item.help
                else _("No help given... (You should report this)")
            ).capitalize()
            + badges,
        )
        return

    async def format_page(
        self, menu: ShakePages | ui.View, items: list[commands.Command]
    ):
        config = configurations(self.bot)
        embed = ShakeEmbed.default(
            menu.ctx,
            title=self.title,
            description=self.description + "\n\u200b",
        )
        embed.set_author(
            name=_("Page {current} of {max} ({entries} subcommands)").format(
                current=menu.page + 1,
                max=self.get_max_pages(),
                entries=len(self.entries),
            )
        )
        for item in items:
            self.add_field(embed, item, config=config)

        last_embed = [
            "**{0}・{1}**".format(config[key].get("suffix"), config[key].get("text"))
            for key in self.suffixes
        ]
        if bool(last_embed):
            embed.add_field(name="\u200b", value="\n".join(last_embed))

        return embed, None


class Front(FrontPageSource):
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
        embed = ShakeEmbed.default(
            menu.ctx,
            title=(
                _("{emoji} Bot Help (Timeouted type ?help again!)")
                if self.timeouted
                else _("{emoji} Bot Help")
            ).format(
                emoji=PartialEmoji(animated=True, name="thanks", id=984980175525666887)
            ),
        )
        if self.index in [1, 2]:
            embed.description = _(
                """Hello and welcome to my help page {emoji}
                Type `{prefix}help <command/category>` to get more information on a\ncommand/category."""
            ).format(emoji="", prefix=menu.ctx.clean_prefix)
            embed.add_field(
                name=_("Support Server"),
                inline=False,
                value=_(
                    "You can get more help if you join the official server at\n{support_server}"
                ).format(support_server=menu.ctx.bot.config.other.server),
            )
        file = None
        if self.index == 0:
            embed.set_image(
                url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png"
            )
            embed.add_field(
                name=_("Who am I?"),
                inline=False,
                value=_(
                    """{user}, which is partially intended for the public.
                    Written with only `{lines}` lines of code. Please be nice"""
                ).format(
                    user=menu.ctx.bot.user.mention,
                    lines="{0:,}".format(menu.ctx.bot.lines),
                ),
            )
        elif self.index == 1:
            embed.add_field(
                name=_("What am I for?"),
                inline=False,
                value=_(
                    """I am a functional all-in-one bot that will simplify setting up your server for you!

                    I have been created {created_at} & 
                    I have functions like voting, level system, music, moderation & much more. 
                    You can get more information by using the dropdown menu below.
                    dropdown menu."""
                ).format(created_at=format_dt(menu.ctx.bot.user.created_at, "F")),
            )
        elif self.index == 2:
            entries = (
                (
                    "<" + _("argument") + ">",
                    _("Stands for the argument being __**necessary**__."),
                ),
                (
                    "[" + _("argument") + "]",
                    _("Stands for that the argument is __**optional**__."),
                ),
                ("[A|B]", _("Stands for the argument can be __**either A or B**__.")),
                (
                    f"[{_('argument')}]…",
                    _(
                        """Stands for the fact that you can use multiple arguments.

                    Now that you know the basics, you should still know that...
                    __**You don't include the parentheses!**__"""
                    ),
                ),
            )
            embed.add_field(
                name=_("How do I use the bot?"),
                value=_("Reading the bot structure is pretty easy."),
            )
            for name, value in entries:
                embed.add_field(name=name, value=value, inline=False)
        return embed, file


#
############
