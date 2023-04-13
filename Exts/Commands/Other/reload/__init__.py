############
#
from discord import PartialEmoji
from importlib import reload as libreload
from . import reload
from Classes import (
    ShakeContext, ShakeBot, ValidCog, extras, _, 
    locale_doc, setlocale
)
from discord.ext.commands import (
    guild_only, is_owner, Greedy, Cog, 
    hybrid_command
)
########
#
class extensions_reload_extension(Cog):
    def __init__(self, bot) -> None: self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}'))
    
    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name="reload")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def reload(self, ctx: ShakeContext, *, extension: Greedy[ValidCog]):
        _(
            """Reload extensions of the bot
            
            Parameters
            -----------
            extension: Greedy[ValidCog]
                the extension"""
        )
        libreload(reload)
        return await reload.command(ctx=ctx, extension=extension).__await__()
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(extensions_reload_extension(bot))
#
############