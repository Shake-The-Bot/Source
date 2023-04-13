############
#
from discord import ActivityType, Activity
from logging import getLogger
from Classes import ShakeBot

logger = getLogger(__name__)
########
#
class topgg_event():
    def __init__(self, bot: ShakeBot, data: dict):
        self.bot: ShakeBot = bot
        self.data: dict = data
    
    async def __await__(self):
        """This functions is called whenever someone votes for the bot on Top.gg"""
        logger.info(
            'Received a vote: {data}'.format(self.data)
        )
#
############