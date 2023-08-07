############
#
from discord import ButtonStyle, File, PartialEmoji, ui

from Classes import ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx)
        embed.set_author(
            name=_("The Shake Team and I thank you for your interest"),
            # icon_url=PartialEmoji(
            #     animated=True, name="bluehearts", id=1052299642961932378
            # ).url,
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060311122751782992/collerbanertomm2.png"
        )
        return await self.ctx.chat(
            embed=embed, view=Link(link=self.bot.config.bot.authentication)
        )


class Link(ui.View):
    def __init__(self, link):
        super().__init__(timeout=None)
        self.add_item(
            ui.Button(
                style=ButtonStyle.blurple,
                emoji=PartialEmoji(name="arrow", id=1093146865706479756),
                label=_("Add Shake to your server"),
                url=link,
            )
        )
        self.add_item(
            ui.Button(
                style=ButtonStyle.blurple,
                emoji=PartialEmoji(name="arrow", id=1093146865706479756),
                label=_("Join Shake's Server"),
                url=link,
            )
        )


#
############
