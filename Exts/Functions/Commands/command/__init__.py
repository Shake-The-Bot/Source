############
#
from importlib import reload
from . import command, testing
from Classes import ShakeContext, ShakeBot, Testing
from discord.ext.commands import Cog
########
#
class on_command(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_command(self, ctx: ShakeContext): # wurde nicht eingetragen
        test = any(x.id in list(self.bot.tests.keys()) for x in (ctx.author, ctx.guild, ctx.channel))
        
        if test:
            reload(testing)
        do = testing if test else command

        try:
            await do.event(ctx=ctx, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_command(bot))
#
############