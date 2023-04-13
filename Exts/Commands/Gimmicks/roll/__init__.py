############
#
from typing import Optional
from . import roll
from discord import PartialEmoji
from importlib import reload
from discord import app_commands
from Classes.i18n import _, locale_doc, setlocale
from Classes import ShakeBot, ShakeContext
from discord.ext import commands
########
#
class roll_extension(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GAME DIE}'))

    def category(self) -> str: 
        return "gimmicks"

    @commands.hybrid_command(name="roll")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def roll(self, ctx: ShakeContext, start: Optional[int] = 1, limit: Optional[int] = 6):
        _(
            """Displays a random number in a specified range of values. (Default: 1-6)

            Parameters
            -----------
            start: Optional[int]
                the start to roll at

            limit: Optional[int]
                the limit to roll till"""
        )
        if self.bot.dev:
            reload(roll)
        return await roll.command(ctx=ctx, start=start or 5, limit=limit or 6).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(roll_extension(bot))
#
############