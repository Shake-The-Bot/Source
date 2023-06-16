############
#
from copy import copy

from Classes import ShakeCommand


########
#
class command(ShakeCommand):
    def __init__(self, ctx, times: int, command: str):
        super().__init__(ctx)
        self.times = times
        self.command = command

    async def __await__(self):
        msg = copy(self.ctx.message)
        msg.content = self.ctx.prefix + self.command
        new_ctx = await self.bot.get_context(msg, cls=type(self.ctx))

        for _ in range(self.times):
            await new_ctx.reinvoke()
