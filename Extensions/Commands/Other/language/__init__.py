############
#
from gettext import GNUTranslations
from importlib import reload
from itertools import chain
from typing import Optional

from discord import Interaction, PartialEmoji, app_commands
from discord.ext.commands import MissingPermissions, guild_only, hybrid_group
from discord.ext.tasks import loop

from Classes import (
    MISSING,
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
            # await rtfm.build_rtfm_lookup_table(self.bot)
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None

        languages = dict(
            (locale.language.lower(), locale) for locale in self.locales.values()
        )
        simples = dict(
            (locale.simplified.lower(), locale) for locale in self.locales.values()
        )
        matches = finder(current, list(chain(self.bot.cache["rtfm"].values())))[:10]
        return [app_commands.Choice(name=m, value=m) for m in matches]

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

    @hybrid_group(name="language", aliases=["lang"], invoke_without_command=True)
    @guild_only()
    @setlocale()
    @locale_doc
    async def language(self, ctx: ShakeContext, language: str):
        return await self.set(ctx, language=language)

    @language.command(name="list")
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

    @language.command(name="set")
    @guild_only()
    @setlocale()
    @locale_doc
    async def set(
        self, ctx: ShakeContext, *, language: str, server: Optional[bool] = False
    ) -> None:
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

    @language.command(name="reset")
    @guild_only()
    @setlocale()
    @locale_doc
    async def reset(self, ctx: ShakeContext, *, server: Optional[bool] = False) -> None:
        _(
            """Reset your language for Shake to the good old language
            Doesn't change anything if no language is set
            
            Parameters
            -----------
            server: Optional[bool]
                If the language should be reset for the whole server"""
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
                    for perm, value in {"administrator": True}.items()
                    if getattr(ctx.permissions, perm) != value
                ]:
                    raise MissingPermissions(missing)
                await do.command(ctx=ctx).set_locale(
                    name=ctx.bot.i18n.default, locales=self.locales, guild=True
                )

            else:
                await do.command(ctx=ctx).set_locale(
                    name=ctx.bot.i18n.default,
                    locales=self.locales,
                )

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(language_extension(bot))


#
############
