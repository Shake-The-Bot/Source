############
#
from discord import Member

from Classes import ShakeBot, ShakeContext, ShakeEmbed

########
#


class command:
    def __init__(self, ctx, member: Member):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.member: Member = member

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        await self.ctx.chat(embed)


#
############
