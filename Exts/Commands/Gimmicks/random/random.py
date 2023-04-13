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
        online = list(filter(lambda u: (True if self.offline else u.status == Status.online) and u.bot == False, self.ctx.guild.members))
        return await self.ctx.invoke(self.bot.get_command('userinfo'), user=choice(online))
#
############