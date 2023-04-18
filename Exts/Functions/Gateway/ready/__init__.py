############
#
from . import ready
from discord.ext.commands import Cog
from Classes import ShakeBot
########
#
class on_ready(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_ready(self):
        try:
            await ready.event(bot=self.bot).__await__()
        except:
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_ready(bot))
#
############