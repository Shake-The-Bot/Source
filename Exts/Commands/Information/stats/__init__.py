############
#
from discord import PartialEmoji
from importlib import reload
from . import stats, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
from Classes import ShakeContext, _, locale_doc, setlocale, Testing, ShakeBot
########
#
class stats_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{CHART WITH UPWARDS TREND}')
    
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

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else stats

        try:    
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot): 
    await bot.add_cog(stats_extension(bot))
#
############