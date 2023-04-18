############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from . import language as lang, testing
from typing import Optional
from discord.ext.commands import MissingPermissions, guild_only, Cog, hybrid_group
########
#
class language_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{EARTH GLOBE EUROPE-AFRICA}')

    def category(self) -> str: 
        return "information"
    
    @hybrid_group(name="language")
    @guild_only()
    @setlocale()
    @locale_doc
    async def language(self, ctx: ShakeContext):
        return

    @language.command(name='list')
    @guild_only()
    @setlocale()
    @locale_doc
    async def list(self, ctx: ShakeContext) -> None:
        _(
            """Display a list of availible languages and locale codes.
            
            You can check if your language is available by comparing against [this list](https://saimana.com/list-of-country-locale-code/)
            Some of these languages are no real languages but serve as a way to spice up the text.
            (If something is not yet translated, the english original text is used.)"""
        )
        
        if ctx.testing:
            reload(testing)

        do = testing if ctx.testing else lang

        try:
            await do.command(ctx=ctx).list()
        except:
            if ctx.testing:
                raise Testing
            raise


    @language.command(name='set')
    @guild_only()
    @setlocale()
    @locale_doc
    async def set(self, ctx: ShakeContext, *, language: str, server: Optional[bool] = False) -> None:
        _(
            """Set your language for Shake.
            Full list of available languages can be found with `{prefix}language`
            
            Parameters
            -----------
            language: str
                The locale code of the language you want to use
            
            server: Optional[bool]
                If the language should be for the whole server"""
        )
        
        if ctx.testing:
            reload(testing)

        do = testing if ctx.testing else lang

        try:        
            if server == True:
                if (missing := [perm for perm, value in {'administrator': True}.items() if getattr(ctx.permissions, perm) != value]):
                    raise MissingPermissions(missing)
                await do.command(ctx=ctx).guild_locale(locale=language)
                
            else:
                await do.command(ctx=ctx).user_locale(locale=language)
            
        except:
            if ctx.testing:
                raise Testing
            raise




async def setup(bot: ShakeBot): 
    await bot.add_cog(language_extension(bot))
#
############