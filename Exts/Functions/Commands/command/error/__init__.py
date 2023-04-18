############
#
from importlib import reload
from . import command_error, testing
from typing import Union
from discord.ext.commands import Cog, CommandError
from Classes import ShakeContext, ShakeBot, Testing
from discord import Interaction
########
#
class on_command_error(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_command_error(self, ctx: Union[ShakeContext, Interaction], error: CommandError):
        if isinstance(ctx, ShakeContext) and ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return
        
        test = any(x.id in list(self.bot.tests.keys()) for x in (ctx.author, ctx.guild, ctx.channel))
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else command_error

        try:
            await do.event(ctx=ctx, error=error).__await__()
    
        except:
            if test:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(on_command_error(bot))
#
############