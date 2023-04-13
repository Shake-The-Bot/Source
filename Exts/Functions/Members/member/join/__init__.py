############
#
from discord import Member
from . import do
from importlib import reload
from Classes import ShakeBot
from discord.ext import commands
########
#
class on_member_join(commands.Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if self.bot.dev:
            reload(do)
        return await do.on_member_join_event(member=member, bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_member_join(bot))
#
############