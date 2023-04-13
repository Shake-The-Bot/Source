############
#
from discord.ext import commands
from Classes import ShakeContext, ShakeBot
########
#
class command_completion_event():
    def __init__(self, ctx: ShakeContext, bot: commands.Bot):
        self.bot: ShakeContext = bot
        self.ctx: ShakeBot = ctx
    
    async def __await__(self):
        if not self.ctx.done: 
            self.ctx.done = True
#
############