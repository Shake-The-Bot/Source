############
#
from Classes import ShakeBot

########
#
class Event():
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
    
    async def __await__(self):
        self.bot.log.info(
            '{name} is successfully divided into {shards} shard(s). ({guilds} server & {users} users)'.format(
                name=self.bot.user.name, shards=len(self.bot.shards), guilds=len(self.bot.guilds), users=len(self.bot.users)
            )
        )
#
############