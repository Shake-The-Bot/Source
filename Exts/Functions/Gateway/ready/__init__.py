############
#
from . import ready
from importlib import reload
from discord.ext.commands import Cog
from Classes import ShakeBot
########
#
class on_ready(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(ready)
        except:
            pass

    @Cog.listener()
    async def on_ready(self):
        try:
            await ready.Event(bot=self.bot).__await__()
        except:
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_ready(bot))
#
############