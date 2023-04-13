############
#
from discord import RawReactionActionEvent
from Classes import ShakeBot
########
#
class raw_reaction_remove_event():
    def __init__(self, bot: ShakeBot, payload: RawReactionActionEvent):
        self.bot: ShakeBot = bot
        self.payload: RawReactionActionEvent = payload
    
    async def __await__(self):
        pass
#
############