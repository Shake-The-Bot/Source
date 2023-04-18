############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional
from . import tempvoice, testing
from discord.ext.commands import Cog, hybrid_group, guild_only, has_permissions
from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale, extras
########
#
class tempvoice_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEAR}')

    @hybrid_group(name="tempvoice")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def tempvoice(self, ctx: ShakeContext) -> None:
        _(
            """Manage the tempvoice features of Shake"""
        )
        pass

    @tempvoice.command(name="setup")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(
        self, ctx: ShakeContext, 
        prefix: Optional[str] = '📞︱', suffix: Optional[str] = None, 
        locked: Optional[bool] = False, user_limit: Optional[int] = None
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
        
        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else tempvoice

        try:    
            await do.command(ctx=ctx, prefix=prefix, suffix=suffix, locked=locked, user_limit=user_limit).setup()
    
        except:
            if ctx.testing:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(tempvoice_extension(bot))
#
############