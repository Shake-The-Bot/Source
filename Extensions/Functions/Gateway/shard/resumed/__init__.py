############
#
from importlib import reload

from discord.ext.commands import Cog

from Classes import ShakeBot

from . import shard_resumed


########
#
class on_shard_resumed(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(shard_resumed)
        except:
            pass

    @Cog.listener()
    async def on_shard_resumed(self, shard_id):
        try:
            await shard_resumed.Event(bot=self.bot, shard_id=shard_id).__await__()
        except:
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_shard_resumed(bot))


#
############
