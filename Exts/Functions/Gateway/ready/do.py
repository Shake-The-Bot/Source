############
#
from discord import ActivityType, Activity
from logging import getLogger
from Classes import ShakeBot

logger = getLogger(__name__)
########
#
class ready_event():
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
    
    async def __await__(self):
        await self.bot.change_presence(activity=Activity(type=getattr(ActivityType, self.bot.config.bot.presence[0], ActivityType.listening), name=self.bot.config.bot.presence[1]))
        logger.info(
            '{name} is successfully divided into {shards} shards. ({guilds} server & {users} users)'.format(
                name=self.bot.user.name, shards=len(self.bot.shards), guilds=len(self.bot.guilds), users=len(self.bot.users)
            )
        )
#
############