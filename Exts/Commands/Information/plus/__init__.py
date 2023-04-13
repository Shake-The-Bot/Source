############
#
from discord import PartialEmoji
from importlib import reload
from . import plus
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class premium_extension(Cog):
    def __init__(self, bot) -> None:  self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEM STONE}'))

    def category(self) -> str: 
        return "information"
    
    @hybrid_command(name="premium", aliases=["shake+",])
    @extras(beta=True, owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def premium(self, ctx: ShakeContext):
        _(
            """Get information about Shake+.

            Of course, you dont have to. It's like a tip"""
        )
        if self.bot.dev:
            reload(plus)
        return await plus.premium_command(ctx=ctx).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(premium_extension(bot))
#
############