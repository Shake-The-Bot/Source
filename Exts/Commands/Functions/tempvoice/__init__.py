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
class tempvoice_extension(commands.Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEAR}'))

    @commands.hybrid_group(name="tempvoice")
    @app_commands.guild_only()
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def tempvoice(self, ctx: ShakeContext) -> None:
        _(
            """Manage the tempvoice features of Shake"""
        )
        pass

    @tempvoice.command(name="setup")
    @commands.has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(self, 
        ctx: ShakeContext, 
        prefix: Optional[str] = '📞︱', 
        suffix: Optional[str] = None, 
        locked: Optional[bool] = False, 
        user_limit: Optional[int] = None
    ) -> None:
        _(
            """Set up TempVoice with a wizard in seconds.

            Parameters
            -----------
            prefix: Optional[strl]
                the prefix

            suffix: Optional[str]
                the suffix

            locked: Optional[bool]
                if locked

            user_limit: Optional[int]
                the user limit
            """
        )
        if self.bot.dev:
            reload(do)
        await do.tempvoice_command(ctx=ctx, prefix=prefix, suffix=suffix, locked=locked, user_limit=user_limit).setup()
    
async def setup(bot): 
    await bot.add_cog(tempvoice_extension(bot))
#
############