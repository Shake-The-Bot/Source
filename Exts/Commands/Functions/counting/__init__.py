############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional
from . import do
from Classes.i18n import _, locale_doc, setlocale
from discord import app_commands
from discord.ext import commands
from Classes import ShakeBot, ShakeContext
########
#
class counting_extension(commands.Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEAR}'))

    @commands.hybrid_group(name="counting")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def counting(self, ctx: ShakeContext) -> None:
        _(
            """Manage the counting features of Shake"""
        )
        pass

    
    @counting.command(name="setup")
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(
        self, ctx: ShakeContext, hardcore: Optional[bool] = False, numbersonly: Optional[bool] = None, goal: Optional[int] = False) -> None:
        _(
            """Set up Counting with a wizard in seconds.

            Parameters
            -----------
            hardcore: Optional[bool]
                if hardcore

            numbersonly: Optional[bool]
                if numbersonly

            goal: Optional[int]
                the goal
            """
        )
        if self.bot.dev:
            reload(do)
        await do.counting_command(ctx=ctx, hardcore=hardcore, numbersonly=numbersonly, goal=goal).setup()
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(counting_extension(bot))
#
############