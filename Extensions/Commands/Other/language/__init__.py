############
#
from gettext import GNUTranslations
from importlib import reload
from typing import Dict, Optional

from discord import Interaction, app_commands
from discord.ext.commands import MissingPermissions, guild_only, hybrid_command
from discord.ext.tasks import loop

from Classes import (
    Locale,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    finder,
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
        self.locales = list()

        try:
            reload(lang)
        except:
            pass

        self.fetch.start()
        self.bot.loop.create_task(self.fetch())

    async def language_slash_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not bool(self.locales):
            await interaction.response.autocomplete([])
            await self.fetch()
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None
        languages = dict(
            (locale.language.lower(), locale) for locale in self.locales.values()
        )
        simplified = dict(
            (locale.simplified.lower(), locale) for locale in self.locales.values()
        )
        added: Dict[str, Locale] = languages | simplified
        matches = finder(current, list(added.keys()))[:10]
        return [
            app_commands.Choice(name=added.get(m).language, value=added.get(m))
            for m in matches
        ]

    async def cog_unload(self) -> None:
        self.fetch.stop()

    @loop(minutes=60)
    async def fetch(self):
        locales = dict()

        for name, translation in translations.items():
            # if not isinstance(translation, GNUTranslations):
            #     continue

            locale = Locale(bot=self.bot, locale=name)
            assert not locale.exists is False
            locales[name] = locale

        self.locales = locales

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
                await do.command(ctx=ctx).set_locale(
                    name=language, locales=self.locales, guild=True
                )

            else:
                await do.command(ctx=ctx).set_locale(
                    name=language, locales=self.locales
                )

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
            await do.command(ctx=ctx).list(locales=self.locales)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(language_extension(bot))


#
############
