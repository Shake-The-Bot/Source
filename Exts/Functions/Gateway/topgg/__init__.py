############
#
from importlib import reload
from . import do
from logging import getLogger
from Classes import ShakeBot
from discord.ext import commands, tasks
logger = getLogger(__name__)
########
#
class topgg_extension(commands.Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @commands.Cog.listener()
    async def on_autopost_success(self):
        logger.info(f"Posted server count ({self.bot.topggpy.guild_count}), shard count ({self.bot.shard_count})")

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            self.bot.dispatch("dbl_test", data)
            return
        if self.bot.dev:
            reload(do)
        return await do.topgg_event(bot=self.bot, data=data).__await__()

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        logger.info(f'Received a test vote:\n{data}')
        return
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(topgg_extension(bot))
#
############