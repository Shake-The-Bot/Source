############
#
from time import monotonic, perf_counter
from typing import Optional

from discord import PartialEmoji, ui

from Classes import Format, ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx)
        embed.title = _('Waiting for the "Pong! 🏓"')

        start = monotonic()
        await self.ctx.typing()
        end = monotonic()
        typing = round((end - start) * 1000)

        start = perf_counter()
        message = await self.ctx.chat(embed=embed)
        end = perf_counter()
        messaging = round((end - start) * 1000)

        bot = round(self.bot.latency * 1000)

        start = perf_counter()
        await self.bot.pool.fetch("SELECT 1")
        end = perf_counter()
        postgres = round((end - start) * 1000)

        pings = (
            typing,
            messaging,
            postgres,
            bot,
        )
        average = round(sum(pings) / len(pings))

        embed = ShakeEmbed.default(
            self.ctx,
            title=_("Pong! 🏓"),
        )
        embed.add_field(
            name=_("Discord Gateway"),
            value=Format.blockquotes(Format.bold("{}ms".format(bot))),
        )
        embed.add_field(
            name=_("Discord Typing"),
            value=Format.blockquotes(Format.bold("{}ms".format(typing))),
        )
        embed.add_field(
            name=_("Discord Messaging"),
            value=Format.blockquotes(Format.bold("{}ms".format(messaging))),
        )
        embed.add_field(
            name=_("Postgres Database"),
            value=Format.blockquotes(Format.bold("{}ms".format(postgres))),
        )
        embed.add_field(
            name=_("Average Latency"),
            value=Format.blockquotes(Format.bold("{}ms".format(average))),
        )

        await message.edit(embed=embed, view=Link("https://discordstatus.com/"))


class Link(ui.View):
    def __init__(self, link):
        super().__init__()
        self.add_item(
            ui.Button(
                emoji=PartialEmoji(
                    name="\N{PERSONAL COMPUTER}",
                ),
                label=_("Discord Status"),
                url=link,
            )
        )


#
############
