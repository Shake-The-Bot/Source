############
#
from importlib import reload
from statcord import Client
from typing import Coroutine, Any
from . import command, testing
from Classes import ShakeContext, ShakeBot, Testing, MISSING
from discord.ext.commands import Cog
########
#

class StatClient(Client):
    def on_error(self, error: BaseException) -> Coroutine[Any, Any, None]:
        return None

class on_command(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            self.api: StatClient = StatClient(bot=self.bot, token=self.bot.config.statcord.key, mem=False, cpu=False)
        except:
            self.api = MISSING
        else:
            self.api.start_loop()
    
    async def cog_unload(self):
        await self.api.session.close()

    @Cog.listener()
    async def on_command(self, ctx: ShakeContext): # wurde nicht eingetragen
        test = any(x.id in set(self.bot.cache['testing'].keys()) for x in [ctx.author, ctx.guild, ctx.channel])
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else command

        try:
            await do.Event(ctx=ctx, bot=self.bot, api=self.api).__await__()
    
        except:
            if test:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_command(bot))
#
############