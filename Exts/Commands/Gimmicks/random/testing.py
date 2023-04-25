############
#
from random import choice
from typing import Optional
from discord import Status
from Classes.i18n import _
from Classes import ShakeContext, ShakeBot
########
#
class command():
    def __init__(self, ctx: ShakeContext, offline: Optional[bool]):
        self.offline: Optional[bool] = offline
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        users = list(
            filter(
                lambda user: (True if self.offline else user.status == Status.online) and user.bot == False, 
                self.ctx.guild.members
            )
        )
        return await self.ctx.invoke(self.bot.get_command('userinfo'), user=choice(users))
#
############