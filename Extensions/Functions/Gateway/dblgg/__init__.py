############
#
from importlib import reload

from discord.ext.commands import Cog
from discord.ext.tasks import loop
from topgg import DBLClient, WebhookManager
from topgg.types import BotVoteData

from Classes import ShakeBot

from . import dblgg


########
#
class topgg_extension(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

        if not hasattr(self.bot, "topggpy"):
            self.bot.topggpy = DBLClient(bot, bot.config.other.topgg.token)

        # if not hasattr(self.bot, "webhook"):
        #     self.bot.webhook = WebhookManager(bot).dbl_webhook(
        #         route="/dbl", auth_key="password"
        #     )
        #     self.bot.webhook.run(9590)

        try:
            reload(dblgg)
        except:
            pass

        if not self.update_stats.is_running:
            self.update_stats.start()

    @loop(minutes=30)
    async def update_stats(self):
        await self.bot.topggpy.post_guild_count()

    @Cog.listener()
    async def on_autopost_success(self):
        self.bot.log.info(
            f"Posted server count ({self.bot.topggpy.guild_count}), shard count ({self.bot.shard_count})"
        )

    @Cog.listener()
    async def on_dbl_vote(self, data: BotVoteData):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        # if data["type"] == "test":
        #     self.bot.dispatch("dbl_test", data)
        #     return

        reload(dblgg)

        try:
            await dblgg.Event(bot=self.bot, data=data).__await__()

        except:
            raise

    @Cog.listener()
    async def on_dbl_test(self, data: BotVoteData):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        self.bot.log.info(f"Received a test vote:\n{data}")


async def setup(bot: ShakeBot):
    await bot.add_cog(topgg_extension(bot))


#
############
