############
#
from random import randint
from discord import PartialEmoji
from Classes.i18n import _
from Classes import ShakeContext, ShakeBot, ShakeEmbed
########
#
class command():
    def __init__(self, ctx: ShakeContext, start: int = 1, end: int = 6):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.end: int = end
        self.start: int = start

    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx, description = _("You have rolled a random number and the result is __**{number}**__").format(number=randint(1, self.end)))
        embed.set_author(
            name=_(f"Dice roll"),
            icon_url=PartialEmoji(animated=True, name='roll', id=1052677647030829056).url
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/946862628179939338/1060311123095732424/collerbanertomm3.png")
        return await self.ctx.smart_reply(embed=embed)
#
############