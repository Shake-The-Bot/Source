############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import do
from typing import Optional
from Classes.i18n import _, locale_doc, setlocale
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from discord import app_commands
########
#
class language_extension(commands.Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{EARTH GLOBE EUROPE-AFRICA}'))

    def category(self) -> str: 
        return "information"
    
    @commands.hybrid_group(name="language")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def language(self, ctx: ShakeContext):
        return

    @language.command(name='list')
    @setlocale()
    @locale_doc
    async def list(self, ctx: ShakeContext) -> None:
        _(
            """Display a list of availible languages and locale codes.
            
            You can check if your language is available by comparing against [this list](https://saimana.com/list-of-country-locale-code/)
            Some of these languages are no real languages but serve as a way to spice up the text.
            (If something is not yet translated, the english original text is used.)"""
        )
        if self.bot.dev:
            reload(do)
        return await do.command(ctx=ctx).list()


    @language.command(name='set')
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
        if self.bot.dev:
            reload(do)
        if server == True:
            
            if (missing := [perm for perm, value in {'administrator': True}.items() if getattr(ctx.permissions, perm) != value]):
                raise MissingPermissions(missing)
            
            await do.command(ctx=ctx).guild_locale(locale=language)
            return

        await do.command(ctx=ctx).user_locale(locale=language)
        return


async def setup(bot: ShakeBot): 
    await bot.add_cog(language_extension(bot))
#
############