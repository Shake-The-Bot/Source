############
#
from discord.ext import commands
from random import random
from Classes import ShakeContext, ShakeBot, _
########
#
class event():
    def __init__(self, ctx: ShakeContext, bot: commands.Bot):
        self.bot: ShakeBot = bot
        self.ctx: ShakeContext = ctx
    
    async def __await__(self):
        if not self.ctx.done: 
            self.ctx.done = True
        
        if random() < (1 / 100):
            content = '*'+ _("Enjoying using Shake? I would love it if you </voted:1056920829620924439> for me or **share** me to your friends!").format(votelink=self.bot.config.other.vote)+'*'
            await self.ctx.send(content=content)
#
############