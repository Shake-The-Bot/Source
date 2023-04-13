############
#
from discord import PartialEmoji
from importlib import reload
from . import do
from Classes.i18n import _, locale_doc, setlocale
from discord import app_commands
from discord.ext import commands
from Classes import ShakeBot, ShakeContext
########
#
class aboveme_extension(commands.Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEAR}'))

    @commands.hybrid_group(name="aboveme")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def aboveme(self, ctx: ShakeContext) -> None:
        _(
            """Manage the aboveme features of Shake"""
        )
        pass

    @aboveme.command(name="setup")
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(
        self, ctx: ShakeContext
    ) -> None:
        _(
            """Set up the Aboveme-Game with a wizard in seconds."""
        )
        if self.bot.dev:
            reload(do)
        await do.aboveme_command(ctx=ctx).setup()
    
async def setup(bot): 
    await bot.add_cog(aboveme_extension(bot))
#
############