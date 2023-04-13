############
#
from importlib import reload
from discord import Interaction
from Classes import ShakeBot
from . import do
from discord.ext import commands
########
#
class on_interaction(commands.Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if self.bot.dev:
            reload(do)
        return await do.interaction_event(bot=self.bot, interaction=interaction).__await__()

async def setup(bot): 
    await bot.add_cog(on_interaction(bot))
#
############