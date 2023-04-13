############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras
from . import dispatch
from typing import Optional
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class dispatch_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{PISTOL}'))
    
    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name="dispatch")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def dispatch(self, ctx: ShakeContext, event: Optional[str], kwargs):
        _(
            """Send an event

            Parameters
            -----------
            event: Optional[str]
                the name of the event

            kwargs: Any
                event keyword arguments"""
        )
        if self.bot.dev:
            reload(dispatch)
        return await dispatch.command(ctx, event, kwargs).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(dispatch_extension(bot))
#
############