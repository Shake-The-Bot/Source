############
#
from importlib import reload
from . import do
from discord.ext import commands
########
#
class on_ready(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if self.bot.dev:
            reload(do)
        return await do.ready_event(bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_ready(bot))
#
############