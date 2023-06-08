from Classes import ShakeBot

############
#


class Event:
    def __init__(self, bot: ShakeBot, shard_id: int):
        self.bot: ShakeBot = bot
        self.shard_id: int = shard_id

    async def __await__(self):
        # logger.info("Shard ID {id} has LOST Connection to Discord.".format(id=shard_id))
        pass


#
############
