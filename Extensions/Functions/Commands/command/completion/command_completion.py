############
#
from random import random

from Classes import ShakeBot, ShakeContext, TextFormat, _


########
#
class Event:
    def __init__(self, ctx: ShakeContext, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.ctx: ShakeContext = ctx
        self.bot.cache["used_commands"].setdefault(self.ctx.author.id, set())

    async def __await__(self):
        await self.bot.register_command(self.ctx)

        if not self.ctx.done:
            self.ctx.done = True

        if self.ctx.command and not self.ctx.command.extras.get("owner", False):
            self.bot.cache["used_commands"][self.ctx.author.id].add(self.ctx.command)

            if len(self.bot.cache["used_commands"][self.ctx.author.id]) >= 10:
                if random() < (6 / 100):
                    content = TextFormat.italics(
                        _(
                            "Enjoying using Shake? I would love it if you </vote:1056920829620924439> for me or share me to your friends!"
                        ).format(votelink=self.bot.config.other.vote, _="*")
                    )
                    await self.ctx.send(content=content, forced=True)


#
############
