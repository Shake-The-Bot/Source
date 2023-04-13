############
#
from discord import RawReactionActionEvent
from importlib import reload
from . import do
from Classes import ShakeBot
from discord.ext import commands
########
#
class on_raw_reaction_remove(commands.Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if (not payload.guild_id) or (self.bot.get_guild(payload.guild_id).get_member(payload.user_id).bot): 
            return None
        if self.bot.dev:
            reload(do)
        return await do.raw_reaction_remove_event(bot=self.bot, payload=payload).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_raw_reaction_remove(bot))
#
############