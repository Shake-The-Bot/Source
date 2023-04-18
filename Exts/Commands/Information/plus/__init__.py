############
#
from discord import PartialEmoji
from importlib import reload
from . import plus, testing
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras, Testing
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class premium_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None:  
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEM STONE}')

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

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else plus

        try:    
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(premium_extension(bot))
#
############