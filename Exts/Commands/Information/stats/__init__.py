############
#
from discord import PartialEmoji
from importlib import reload
from . import do
from discord.ext.commands import Cog, hybrid_command, guild_only
from Classes import ShakeContext, _, locale_doc, setlocale
########
#
class stats_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{CHART WITH UPWARDS TREND}'))
    
    def category(self) -> str: 
        return "information"

    @hybrid_command(name="stats", aliases=["s"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def stats(self, ctx: ShakeContext):
        _(
            """Get some basic information and statistics about me.
            
            very useful to stalk"""
        )
        if self.bot.dev:
            reload(do)
        return await do.stats_command(ctx=ctx).__await__()

async def setup(bot): 
    await bot.add_cog(stats_extension(bot))
#
############