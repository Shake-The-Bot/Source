############
#
from importlib import reload
from . import count, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
from discord import PartialEmoji
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
########
#
class count_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(count)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INPUT SYMBOL FOR NUMBERS}')
    
    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name='count')
    @guild_only()
    @setlocale()
    @locale_doc
    async def count(self, ctx: ShakeContext):
        _(
            """Count for yourself"""
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else count

        try:    
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(count_extension(bot))
#
############