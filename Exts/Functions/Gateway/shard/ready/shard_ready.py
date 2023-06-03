############
#
from Classes import ShakeBot


########
#
class Event:
    def __init__(self, bot: ShakeBot, shard_id: int):
        self.bot: ShakeBot = bot
        self.shard_id: int = shard_id

    async def __await__(self):
        self.bot.ready_shards.ready(self.shard_id)


#
############
