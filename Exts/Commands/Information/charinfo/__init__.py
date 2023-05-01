############
#
from discord import PartialEmoji
from importlib import reload
from . import charinfo, testing
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext, Testing
########
#
class charinfo_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        try:
            reload(charinfo)
        except:
            pass
    
    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INPUT SYMBOL FOR LATIN SMALL LETTERS}')

    def category(self) -> str: 
        return "information"

    @hybrid_command(name="charinfo")
    @guild_only()
    @setlocale()
    @locale_doc
    async def charinfo(self, ctx: ShakeContext, *, characters: str) -> None:
        _(
            """Displays information about a set of characters.
            
            Parameters
            -----------
            characters: str
                the symbols to get information about"""
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False

        do = testing if ctx.testing else charinfo

        try:
            await do.command(ctx=ctx, characters=characters).__await__()
        
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(charinfo_extension(bot))
#
############