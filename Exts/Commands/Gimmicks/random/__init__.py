############
#
from discord import PartialEmoji
from typing import Optional
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import random
from Classes.i18n import _, locale_doc, setlocale
from discord import app_commands
from discord.ext import commands
########
#
class random_extension(commands.Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{VIDEO GAME}'))

    def category(self) -> str: 
        return "gimmicks"
    
    @commands.hybrid_command(name="random")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def random(self, ctx: ShakeContext, offline: Optional[bool] = True):
        _(
            """Picks a random online user

            Parameters
            -----------
            offline: bool
                if offline is ok"""
        )
        if self.bot.dev:
            reload(random)
        return await random.command(ctx=ctx, offline=offline).__await__()
########
#
async def setup(bot: ShakeBot): 
    await bot.add_cog(random_extension(bot))
#
############