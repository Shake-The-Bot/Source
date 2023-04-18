############
#
from discord import RawReactionActionEvent
from importlib import reload
from . import raw_reaction_remove, testing
from Classes import ShakeBot, Testing
from discord.ext.commands import Cog
########
#
class on_raw_reaction_remove(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if (not payload.guild_id) or (self.bot.get_guild(payload.guild_id).get_member(payload.user_id).bot): 
            return None
        
        test = any(x in list(self.bot.tests.keys()) for x in (payload.channel_id, payload.guild_id, payload.user_id))
        
        if test:
            reload(testing)
        do = testing if test else raw_reaction_remove

        try:
            await do.event(bot=self.bot, payload=payload).__await__()
    
        except:
            if test:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_raw_reaction_remove(bot))
#
############