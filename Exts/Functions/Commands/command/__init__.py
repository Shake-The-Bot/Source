############
#
from importlib import reload
from . import do
from Classes import ShakeContext
from discord.ext import commands
########
#
class on_command(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx: ShakeContext): # wurde nicht eingetragen
        if self.bot.dev:
            reload(do)
        return await do.command_event(ctx=ctx, bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_command(bot))
#
############