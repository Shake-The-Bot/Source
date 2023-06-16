############
#
from typing import Optional

from discord import Status

from Classes import ShakeCommand, _, choice


########
#
class command(ShakeCommand):
    def __init__(self, ctx, offline: Optional[bool]):
        super().__init__(ctx=ctx)
        self.offline: Optional[bool] = offline

    async def __await__(self):
        members = list(
            filter(
                lambda user: (True if self.offline else user.status == Status.online)
                and user.bot == False,
                self.ctx.guild.members,
            )
        )
        return await self.ctx.invoke(
            self.bot.get_command("userinfo"), user=choice(members)
        )


#
############
