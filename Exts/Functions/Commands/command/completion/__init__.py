############
#
from importlib import reload
from . import command_completion, testing
from Classes import ShakeContext, ShakeBot, Testing
from discord.ext.commands import Cog
########
#
class on_command_completion(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_command_completion(self, ctx: ShakeContext):
        
        test = any(x.id in list(self.bot.tests.keys()) for x in (ctx.author, ctx.guild, ctx.channel))
        
        if test:
            reload(testing)
        do = testing if test else command_completion

        try:
            await do.event(ctx=ctx, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise
            
    

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_command_completion(bot))
#
############