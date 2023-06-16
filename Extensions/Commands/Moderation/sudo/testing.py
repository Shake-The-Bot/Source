############
#
from copy import copy
from typing import Any, Optional, Union

from discord import Member, TextChannel, User

from Classes import ShakeCommand


########
#
class command(ShakeCommand):
    def __init__(
        self,
        ctx,
        channel: Optional[TextChannel],
        user: Member | User,
        command: str,
        args: Any = None,
    ):
        super().__init__(ctx)
        self.channel: TextChannel = channel
        self.user: User = user
        self.command: str = command
        self.args = args

    async def __await__(self):
        msg = copy(self.ctx.message)
        new_channel = self.channel or self.ctx.channel
        msg.channel = new_channel
        msg.author = self.user
        msg.content = self.ctx.prefix + self.command + " " + self.args
        new_ctx = await self.bot.get_context(msg, cls=type(self.ctx))
        await self.bot.invoke(new_ctx)
