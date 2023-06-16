############
#
import platform
from datetime import timedelta
from platform import python_version
from time import time
from typing import Any, Dict, List, Tuple

import cpuinfo
from discord import __version__ as discord_version
from discord.ext.commands import Command
from discord.utils import format_dt
from humanize import naturalsize
from psutil import Process, cpu_percent, virtual_memory

from Classes import (
    MISSING,
    ShakeBot,
    ShakeCommand,
    ShakeContext,
    ShakeEmbed,
    TextFormat,
    _,
    __version__,
)
from Classes.pages import (
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
    SourceSource,
)
from Classes.useful import human_join

########
#


class command(ShakeCommand):
    commands: List[Tuple[str, int]]
    bot: ShakeBot
    ctx: ShakeContext

    def __init__(self, ctx, commands):
        super().__init__(ctx)
        self.commands = commands

    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=SourceSource)
        menu = CategoricalMenu(ctx=self.ctx, source=Front(), select=select)
        categories = {
            CommandsSource(ctx=self.ctx, commands=self.commands): self.bot.commands,
            SystemSource(ctx=self.ctx): self,
            BotSource(ctx=self.ctx): self.bot,
        }

        menu.add_categories(categories=categories)
        if await menu.setup():
            await menu.send(ephemeral=True)


class BotSource(ItemPageSource):
    item: ShakeBot

    def __init__(self, ctx: ShakeContext, *args, **kwargs):
        super().__init__(
            ctx,
            item=ctx.bot,
            title=MISSING,
            label=_("Bot"),
            *args,
            **kwargs,
        )

    async def format_page(
        self, menu: CategoricalMenu, args: Any, **kwargs: Any
    ) -> ShakeEmbed:
        embed = ShakeEmbed()
        embed.title = _("Bot Info")

        uptime = format_dt(menu.bot.started, "R")
        embed.add_field(name=_("Started"), value=TextFormat.blockquotes(uptime))
        embed.add_field(
            name=_("Ping"),
            value=TextFormat.bold(
                TextFormat.blockquotes(round(menu.bot.latency * 1000)) + "ms"
            ),
        )
        embed.add_field(
            name=_("Lines of Code"),
            value=TextFormat.bold(TextFormat.blockquotes(menu.bot.lines)),
        )

        embed.add_field(
            name=_("Servers"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(len(menu.bot.guilds), "css")
            ),
        )

        embed.add_field(
            name=_("Users"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(len(menu.bot.users), "css")
            ),
        )

        embed.add_field(
            name=_("Commands"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(len(menu.bot.commands), "css")
            ),
        )

        return embed, None


class SystemSource(ItemPageSource):
    item: Process

    def __init__(self, ctx: ShakeContext, *args, **kwargs):
        super().__init__(
            ctx,
            item=Process(),
            title=MISSING,
            label=_("System"),
            *args,
            **kwargs,
        )

    async def format_page(
        self, menu: CategoricalMenu, args: Any, **kwargs: Any
    ) -> ShakeEmbed:
        embed = ShakeEmbed()
        embed.title = _("System Info")

        embed.add_field(
            name=_("Bot"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock("Shake v " + str(__version__), "css")
            ),
        )

        embed.add_field(
            name=_("Python version"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(python_version(), "css")
            ),
        )

        embed.add_field(
            name=_("Library version"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock("discord.py " + discord_version, "css")
            ),
        )

        with self.item.oneshot():
            uptime = timedelta(seconds=time() - self.item.create_time())
            uptime = uptime - timedelta(microseconds=uptime.microseconds)

            cpu = self.item.cpu_times()
            cpu_time = timedelta(seconds=cpu.system + cpu.user)
            cpu_time = cpu_time - timedelta(microseconds=cpu_time.microseconds)

            mem_total = virtual_memory().total / (1024**2)
            mem_of_total = self.item.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        cpu_usage = str(cpu_percent()).split(".")[0] + "%"
        memory_usage = f"{mem_usage:,.0f} / {mem_total:,.0f} MiB ({mem_of_total:.0f}%)"

        embed.add_field(
            name=_("Memory Usage"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(memory_usage, "css")
            ),
        )
        cpu = " | ".join([str(_) for _ in (cpu_usage, cpu_time)])
        embed.add_field(
            name=_("CPU Usage"),
            value=TextFormat.multiblockquotes(TextFormat.multicodeblock(cpu, "css")),
        )

        embed.add_field(
            name=_("Plattform"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(platform.system(), "css")
            ),
            inline=False,
        )

        return embed, None


class CommandsSource(ListPageSource):
    commands: Dict[str, int]
    ctx: ShakeContext

    def __init__(self, ctx, commands: List[Tuple[str, int]], *args, **kwargs):
        self.commands = dict(
            [(command, uses) for command, uses in commands if uses > 1]
        )
        super().__init__(
            ctx,
            items=list(self.commands.keys()),
            title=MISSING,
            label=_("Commands"),
            paginating=True,
            per_page=30,
            *args,
            **kwargs,
        )

    def format_page(
        self, menu: CategoricalMenu, items: List[Command], **kwargs: Any
    ) -> ShakeEmbed:
        n = len(items) // 2
        first_half, sec_half = (items[:n], items[n:])

        embed = ShakeEmbed()
        embed.add_field(
            name=_("Most used commands"),
            value="\n".join(
                [
                    "` {}. ` {} - {}".format(
                        list(self.commands.keys()).index(command) + 1,
                        TextFormat.bold(self.commands[command]),
                        command,
                    )
                    for command in first_half
                ]
            ),
        )
        embed.add_field(
            name="\u200b",
            value="\n".join(
                [
                    "` {}. ` {} - {}".format(
                        list(self.commands.keys()).index(command) + 1,
                        TextFormat.bold(self.commands[command]),
                        command,
                    )
                    for command in sec_half
                ]
            ),
        )
        return embed, None


class Front(FrontPageSource):
    async def format_page(self, menu: CategoricalMenu, items: Any):
        owners = [
            str(await menu.bot.get_user_global(user_id))
            for user_id in menu.bot.owner_ids
        ]

        embed = ShakeEmbed.default(menu.ctx)
        embed.title = _("Shake Statistics Overview")

        links = [
            TextFormat.hyperlink(
                _("Support Server Link"), menu.bot.config.other.server
            ),
            TextFormat.hyperlink(
                _("Shake Invition Link"), menu.bot.config.other.authentication
            ),
        ]

        embed.description = "\n".join(
            [TextFormat.list(TextFormat.bold(_)) for _ in links]
        )

        if bool(owners):
            embed.add_field(
                name=_("Developer"),
                value=TextFormat.multiblockquotes(
                    TextFormat.multicodeblock(" - ".join(owners), "css")
                ),
                inline=False,
            )

        embed.add_field(
            name=_("Bot name"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(menu.bot.user, "css")
            ),
        )
        embed.add_field(
            name=_("Bot ID"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(menu.bot.user.id, "css")
            ),
        )

        created_at = format_dt(menu.bot.user.created_at, "F")
        embed.add_field(
            name=_("Bot creation"),
            value=TextFormat.blockquotes(created_at),
            inline=False,
        )

        embed.advertise(menu.bot)
        return embed, None


#
############
