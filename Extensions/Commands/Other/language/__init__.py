############
#
from difflib import get_close_matches
from gettext import GNUTranslations
from importlib import reload
from typing import Any, Dict, List, Optional, Union

from discord import Interaction, app_commands
from discord.ext.commands import MissingPermissions, guild_only, hybrid_command
from discord.ext.tasks import loop

from Classes import (
    Format,
    Locale,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    locale_doc,
    setlocale,
    translations,
)

from ..other import Other
from . import language as lang
from . import testing

########
#

EXCEPTION = {"sr-SP": "sr"}


class language_extension(Other):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)

        try:
            reload(lang)
        except:
            pass

    async def language_slash_autocomplete(
        self, interaction: Interaction, current: Optional[str]
    ) -> List[app_commands.Choice[str]]:
        if not bool(self.bot.locales):
            await self.fetch()
            await interaction.response.autocomplete([])
            return []

        if not current:
            return []

        assert not interaction.command is None

        searches: Dict[str, Locale] = (
            self.bot.locales.languages | self.bot.locales.simples
        )
        matches = get_close_matches(current, list(searches.keys()))[:10]
        if bool(matches):
            return list(
                app_commands.Choice(
                    name=locale.specific or locale.language,
                    value=locale.locale,
                )
                for locale in set(searches.get(m) for m in matches)
            )

        if current in searches:
            return [
                app_commands.Choice(
                    name=searches.get(current).specific,
                    value=searches.get(current).specific,
                )
            ]
        else:
            return []

    async def cog_unload(self) -> None:
        self.fetch.stop()

    async def cog_load(self) -> None:
        await self.fetch()
        if not self.fetch.is_running:
            self.fetch.start()

    @loop(minutes=60)
    async def fetch(self):
        locales = [Locale(bot=self.bot, locale=name) for name in translations.keys()]
        self.bot.locales(locales)

    @hybrid_command(name="language", aliases=["lang"])
    @guild_only()
    @app_commands.autocomplete(language=language_slash_autocomplete)
    @setlocale()
    @locale_doc
    async def language(
        self, ctx: ShakeContext, *, language: str, server: Optional[bool] = False
    ):
        _(
            """Set your language for Shake.
            Full list of available languages can be found with `{prefix}language`
            
            Parameters
            -----------
            language: str
                The locale code of the language you want to set
            
            server: Optional[bool]
                If the language should be set for the whole server"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else lang

        try:
            if server == True:
                if missing := [
                    perm
                    for perm, value in {"manage_guild": True}.items()
                    if getattr(ctx.permissions, perm) != value
                ]:
                    raise MissingPermissions(missing)
                await do.command(ctx=ctx).set_locale(name=language, guild=True)

            else:
                await do.command(ctx=ctx).set_locale(name=language)

        except:
            if ctx.testing:
                raise Testing
            raise

    @hybrid_command(name="languages")
    @guild_only()
    @setlocale()
    @locale_doc
    async def languages(self, ctx: ShakeContext) -> None:
        _(
            """Display a list of availible languages and locale codes.
            
            You can check if your language is available by comparing against [this list](https://saimana.com/list-of-country-locale-code/)
            Some of these languages are no real languages but serve as a way to spice up the text.
            (If something is not yet translated, the english original text is used.)"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else lang

        try:
            await do.command(ctx=ctx).list()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(language_extension(bot))


#
############
