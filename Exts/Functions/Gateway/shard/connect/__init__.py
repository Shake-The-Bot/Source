############
#
from importlib import reload

from discord.ext.commands import Cog

from Classes import ShakeBot

from . import shard_connect


########
#
class on_shard_connect(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(shard_connect)
        except:
            pass

    @Cog.listener()
    async def on_shard_connect(self, shard_id):
        try:
            await shard_connect.Event(bot=self.bot, shard_id=shard_id).__await__()
        except:
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_shard_connect(bot))


#
############
