############
#
from discord import PartialEmoji
from importlib import reload
from . import do
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext
from discord import app_commands
from typing import Literal
from discord.ext import commands
from discord.ext.commands import Greedy
########
#
class freegames_commands_extension(commands.Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEAR}'))

    @commands.hybrid_group(name="freegames")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def freegames(self, ctx: ShakeContext) -> None:
        _(
            """Manage the aboveme features of Shake"""
        )
        pass

    @freegames.command(name="setup")
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(self, ctx: ShakeContext, stores: Greedy[Literal['steam', 'epicgames', 'gog']]) -> None:
        _(
            """Set up the Aboveme-Game with a wizard in seconds.
            
            Parameters
            -----------
            stores: Literal['steam', 'epicgames', 'gog']
                the stores which the channel should support
            """
        )
        if self.bot.dev:
            reload(do)
        await do.freegames_command(ctx=ctx, stores=stores).setup()
    
async def setup(bot): 
    await bot.add_cog(freegames_commands_extension(bot))
#
############