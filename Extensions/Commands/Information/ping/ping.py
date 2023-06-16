############
#
from discord import PartialEmoji, ui

from Classes import ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
            title=_("Pong! 🏓"),
        )
        embed.add_field(
            name=_("Discord Gateway"),
            inline=True,
            value="> **{}**ms".format(round(self.bot.latency * 1000)),
        )
        embed.add_field(
            name=_("Client Latency"), inline=True, value="> **{}**ms".format(0)
        )
        await self.ctx.chat(embed=embed, view=Link("https://discordstatus.com/"))


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
