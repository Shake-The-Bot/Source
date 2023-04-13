############
#
from copy import copy
from typing import Optional, Union, Any

from discord import TextChannel, User
from Classes import ShakeBot, ShakeContext
from discord import Member, TextChannel, User
from Classes import ShakeContext
########
#
class sudo_command():
    def __init__(self, ctx: ShakeContext, channel: Optional[TextChannel], user: Union[Member, User], command: str, args: Any=None):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.channel: TextChannel = channel
        self.user: User = user
        self.command: str = command
        self.args = args
    
    async def __await__(self):
        msg = copy(self.ctx.message)
        new_channel = self.channel or self.ctx.channel
        msg.channel = new_channel
        msg.author = self.user
        msg.content = self.ctx.prefix + self.command + ' ' + self.args
        new_ctx = await self.bot.get_context(msg, cls=type(self.ctx))
        await self.bot.invoke(new_ctx)