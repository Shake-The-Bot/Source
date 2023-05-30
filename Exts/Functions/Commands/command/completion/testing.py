############
#
from random import random

from Classes import ShakeBot, ShakeContext, _


########
#
class Event:
    def __init__(self, ctx: ShakeContext, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.ctx: ShakeContext = ctx
        self.bot.cache["used_commands"].setdefault(self.ctx.author.id, 0)

    async def __await__(self):
        await self.bot.register_command(self.ctx)

        if not self.ctx.done:
            self.ctx.done = True

        self.bot.cache["used_commands"][self.ctx.author.id] += 1

        if self.bot.cache["used_commands"][self.ctx.author.id] >= 10:
            if random() < (6 / 100):
                content = _(
                    "{_}Enjoying using Shake? I would love it if you </vote:1056920829620924439> for me or **share** me to your friends!{_}"
                ).format(votelink=self.bot.config.other.vote, _="*")
                await self.ctx.send(content=content, forced=True)


#
############
