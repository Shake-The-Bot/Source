############
#
from importlib import reload
from . import topgg
from logging import getLogger
from Classes import ShakeBot
from discord.ext.commands import Cog
logger = getLogger(__name__)
########
#
class topgg_extension(Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot
        try:
            reload(topgg)
        except:
            pass

    @Cog.listener()
    async def on_autopost_success(self):
        logger.info(f"Posted server count ({self.bot.topggpy.guild_count}), shard count ({self.bot.shard_count})")

    @Cog.listener()
    async def on_dbl_vote(self, data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            self.bot.dispatch("dbl_test", data)
            return
                
        reload(topgg)

        try:
            await topgg.Event(bot=self.bot, data=data).__await__()
    
        except:
            raise



    @Cog.listener()
    async def on_dbl_test(self, data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        logger.info(f'Received a test vote:\n{data}')
        return
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(topgg_extension(bot))
#
############