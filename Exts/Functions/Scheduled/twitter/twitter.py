############
#
from typing import Any
from Classes.i18n import _
from Classes import ShakeBot
########
#
class event():
    def __init__(self, bot: ShakeBot, status: Any, uri: str):
        self.bot: ShakeBot = bot
        self.status: Any = status
        self.uri = uri

    async def __await__(self):
        channel = self.bot.get_channel(1057828685064974376)
        await channel.send(self.status, self.uri)
#
############