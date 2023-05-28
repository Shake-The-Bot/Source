############
#
from Classes import ShakeBot, __version__
from discord.utils import utcnow
########
#
class Event():
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
    
    async def __await__(self):
        self.bot.log.info(
            '{name} is successfully divided into {ready} of {all} shard(s). ({guilds} server & {users} users) [{version}]'.format(
                name=self.bot.user.name, ready=len(self.bot.ready_shards.readies()), all=len(self.bot.shards), guilds=len(self.bot.guilds), users=len(self.bot.users), version=str(__version__)
            )
        )
        if not hasattr(self.bot, 'uptime'):
            self.bot.boot = utcnow()
#
############