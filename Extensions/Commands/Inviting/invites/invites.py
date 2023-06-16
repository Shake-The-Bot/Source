############
#
from discord import Member

from Classes import ShakeCommand, ShakeEmbed

########
#


class command(ShakeCommand):
    def __init__(self, ctx, member: Member):
        super().__init__(ctx)
        self.member: Member = member

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        await self.ctx.chat(embed)


#
############
