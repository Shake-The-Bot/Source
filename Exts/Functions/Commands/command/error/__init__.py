############
#
from importlib import reload
from . import command_error, testing as testfile
from typing import Union, Optional
from discord.ext.commands import Cog, CommandError
from Classes import ShakeContext, ShakeBot, Testing
from discord import Interaction, Client
########
#
class on_command_error(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(command_error)
        except:
            pass

    @Cog.listener()
    async def on_command_error(self, ctx: Union[ShakeContext, Interaction], error: CommandError):
        if isinstance(ctx, ShakeContext) and ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return
        
        author: ShakeBot = ctx.author if isinstance(ctx, ShakeContext) else ctx.user
        test = any(x.id in set(self.bot.cache['testing'].keys()) for x in [author, ctx.guild, ctx.channel])
        
        if test:
            try:
                reload(testfile)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testfile.__file__, type=e.__class__.__name__
                ))
                test = False
        do = testfile if test else command_error

        try:
            await do.Event(ctx=ctx, error=error).__await__()
    
        except:
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(on_command_error(bot))
#
############