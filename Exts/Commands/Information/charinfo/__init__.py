############
#
from discord import PartialEmoji
from importlib import reload
from . import charinfo
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes.i18n import _, locale_doc, setlocale
########
#
class charinfo_extension(Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.env = {}
    
    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{INPUT SYMBOL FOR LATIN SMALL LETTERS}'))
    
    def category(self) -> str: 
        return "information"

    @hybrid_command(name="charinfo", aliases=["ci"],)
    @guild_only()
    @setlocale()
    @locale_doc
    async def charinfo(self, ctx, *, characters: str) -> None:
        _(
            """Displays information about a set of characters.
            
            Parameters
            -----------
            characters: str
                the symbols to get information about"""
        )
        if self.bot.dev:
            reload(charinfo)
        return await charinfo.command(ctx=ctx, characters=characters).__await__()

async def setup(bot): 
    await bot.add_cog(charinfo_extension(bot))
#
############