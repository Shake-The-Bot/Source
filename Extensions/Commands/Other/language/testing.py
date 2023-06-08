############
#
from contextlib import suppress
from gettext import GNUTranslations
from inspect import cleandoc
from os import path
from typing import Union

from discord import PartialEmoji
from polib import pofile

from Classes import (
    MISSING,
    Locale,
    ShakeBot,
    ShakeContext,
    ShakeEmbed,
    _,
    gettext_translations,
    localedir,
    locales,
)
from Classes.pages import ListMenu, ListPageSource

########
#


class L:
    locale: str
    authors: str
    flag: str
    language: str
    two_letters_code: str
    locale_with_underscore: str

    __slots__ = {
        "locale",
        "authors",
        "flag",
        "language",
        "two_letters_code",
        "locale_with_underscore",
        "first_two_letters",
        "bettername",
    }

    def __init__(self, locale: str) -> None:
        po = None
        with suppress(OSError):
            po = pofile(path.join(localedir, locale, "LC_MESSAGES", "shake.po"))
        DC_EXCEPTION = {"sr-SP": "sr"}
        metadata = getattr(po, "metadata", {})
        crw_lang = metadata.pop("X_Crowdin_Language", "")  # ''  /  None
        self.authors = [", ".join(metadata.pop("Last-Translator", "").split())] or []
        self.two_letters_code = metadata.pop(
            "Language", crw_lang[:2] or locale[:2]
        ).lower()  # if crw_lang else
        self.first_two_letters = metadata.pop(
            "Language", crw_lang[3:] or locale[3:]
        ).lower()  # if crw_lang else
        self.language = Locale.available.get(locale, {}).get(
            "language", None
        ) or metadata.pop(
            "Language-Team", None
        )  # .replace(two_letters_code, y.get(two_letters_code, two_letters_code))
        self.flag: str = ":flag_{}:".format(
            DC_EXCEPTION.get(locale, self.first_two_letters)
        )
        self.locale_with_underscore = (
            (
                (crw_lang.lower() + "_" + crw_lang.upper())
                if len(crw_lang) == 2
                else (crw_lang)
            ).replace("-", "_")
            if crw_lang
            else None
        )
        self.locale = locale
        self.bettername = Locale.available.get(locale, {}).get("_", None) or None

    def __str__(self) -> str:
        return self.locale


class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    def get_locale_by_name(self, name: str) -> str:
        for locale in Locale.available.keys():
            language = Locale.available[locale]["language"]
            simplified = Locale.available[locale]["simplified"]
            if name.lower() in [x.lower() for x in [language, locale] + simplified]:
                return locale
        return None

    def check(self, name: str) -> ShakeEmbed | bool:
        locale = self.get_locale_by_name(name)
        if locale is None:
            embed = ShakeEmbed.to_error(
                self.ctx, description=_("Your given language is not valid.")
            )
            embed.description += "\n" + _(
                "Use {command} to get a list of all available languages"
            ).format(command="</language list>")
        elif not name in locales:
            embed = ShakeEmbed.to_error(
                self.ctx,
                description=_(
                    "I'm sorry to say that I dont have your given locale ready."
                ),
            )
            embed.description += "\n" + _(
                "Try to contribute [here]({link}) if you want to!"
            ).format(link="https://github.com/Shake-Developement/Locales/")
            locale = None
        else:
            embed = ShakeEmbed.to_success(
                self.ctx,
                description=_("{name} was successfully set as language!").format(
                    name=Locale.available[locale]["simplified"][-1].capitalize()
                ),
            )
            locale = name
        return embed, locale

    async def list(self):
        items = [
            L(x)
            for x in set(
                x
                for x, y in gettext_translations.items()
                if isinstance(y, GNUTranslations)
            )
        ]
        current = L(
            await self.bot.locale.get_user_locale(self.ctx.author.id) or "en-US"
        )
        menu = ListMenu(
            ctx=self.ctx,
            source=PageSource(
                ctx=self.ctx,
                items=items,
                current=current,
                title=_("Available Translations"),
                description=_(
                    "There are currently translations for `{languages}` languages \nand your current language is **{current}**.\n\n{_}Don't you see your language or is incomplete?{_} \nThen come help us out on [Crowdin]({link})!"
                    ""
                ).format(
                    languages=len(items),
                    link=self.bot.config.other.crowdin,
                    current=current.language,
                    _="_",
                ),
            ),
        )
        await menu.setup()
        await menu.send()

    async def user_locale(self, locale):
        await self.ctx.defer()
        embed, locale = self.check(locale)
        if locale:
            await self.bot.locale.set_user_locale(self.ctx.author.id, locale)
        await self.ctx.chat(embed=embed)
        return

    async def guild_locale(self, locale):
        await self.ctx.defer()
        embed, locale = self.check(locale)
        if locale:
            await self.bot.locale.set_guild_locale(self.ctx.guild.id, locale)
        await self.ctx.chat(embed=embed)
        return


class PageSource(ListPageSource):
    def add_field(self, embed, item: L):
        tick = (
            str(PartialEmoji(name="left", id=1033551843210579988))
            if str(item) == str(self.kwargs.get("current", MISSING))
            else ""
        )
        embed.add_field(
            inline=False,
            name="` {index}. ` {flag} \N{EM DASH} {language} {emoji}".format(
                index=self.items.index(item) + 1,
                flag=getattr(item, "flag", ""),
                language=item.bettername or item.language,
                emoji=tick,
            ),
            value="""{usage} to set this language""".format(
                authors=", ".join(item.authors) or "`/`",
                usage=f"`/language set {item.locale}`",
            ),
        )


#
############
