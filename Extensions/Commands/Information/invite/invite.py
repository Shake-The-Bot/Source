############
#
from discord import ButtonStyle, File, PartialEmoji, ui

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        embed.set_author(
            name=_(f"The Shake Team and I thank you for your interest"),
            icon_url=PartialEmoji(
                animated=True, name="bluehearts", id=1052299642961932378
            ).url,
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060311122751782992/collerbanertomm2.png"
        )
        return await self.ctx.chat(
            embed=embed, view=Link(link=self.bot.config.other.authentication)
        )


class Link(ui.View):
    def __init__(self, link):
        super().__init__(timeout=None)
        self.add_item(
            ui.Button(
                style=ButtonStyle.blurple,
                emoji=PartialEmoji(animated=True, name="arrow", id=1051953224216756284),
                label=_("Add Shake to your Server"),
                url=link,
            )
        )
        self.add_item(
            ui.Button(
                style=ButtonStyle.blurple,
                emoji=PartialEmoji(animated=True, name="arrow", id=1051953224216756284),
                label=_("Join Shake's Server"),
                url=link,
            )
        )


#
############
