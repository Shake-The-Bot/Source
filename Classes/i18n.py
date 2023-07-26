from __future__ import annotations

from contextlib import suppress
from contextvars import ContextVar
from gettext import NullTranslations, gettext, translation
from glob import glob
from os import getcwd, listdir, walk
from os.path import basename, isdir, isfile, join, splitext
from subprocess import call
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from discord import Guild, User
from polib import pofile

from Classes.types import Localization

if TYPE_CHECKING:
    from bot import ShakeBot

__all__ = ("Client", "_", "Locales", "current", "default", "translations", "Locale")
########
#
default: str = "en-US"
translations = dict()

EXCEPTION = {"sr-SP": "sr"}

current: ContextVar[str] = ContextVar("current", default=default)
current.set(default)


class Client:
    default: str
    domain: str
    bot: ShakeBot
    cache: Dict[int, str]

    def __init__(
        self, bot: ShakeBot, domain: str = "shake", directory: str = "Locales"
    ) -> None:
        self.directory = join(getcwd(), directory)
        self.default = default
        self.bot = bot
        bot.cache.setdefault("locales", dict())
        self.cache: Dict = bot.cache["locales"]
        self.domain = domain
        self.translate()
        self.convert()

    def __call__(self) -> None:
        self.translate()
        self.convert()

    @property
    def locales(
        self,
    ) -> frozenset[str]:
        return frozenset(
            map(
                basename,
                filter(isdir, glob(join(getcwd(), self.directory, "*"))),
            )
        ) | {self.default}

    def convert(self) -> list[tuple[str, str]]:
        directories = [self.directory + "/" + l + "/LC_MESSAGES/" for l in self.locales]
        files = []
        for directory in directories:
            paths = filter(
                lambda path: isfile(join(directory, path)) and path.endswith(".po"),
                listdir(directory),
            )
            for path in paths:
                po = join(directory, path)
                filename, extension = splitext(po)
                mo = filename + ".mo"
                cmd = "msgfmt {} -o {}".format(po, mo)
                call(cmd, shell=True)
                files.append(mo)

    def translate(self) -> None:
        for locale in self.locales:
            translations[locale] = translation(
                self.domain,
                languages=(locale,),
                localedir=self.directory,
                fallback=True,
            )

        translations[default] = NullTranslations()

    @staticmethod
    def use(*args: Any, **kwargs: Any) -> str:
        if not bool(args) and not bool(kwargs):
            return None
        if not translations:
            return gettext(*args, **kwargs)
        locale = current.get()
        return translations.get(locale, translations[default]).gettext(*args, **kwargs)

    async def set_user(self, user_id: User.id, locale: str):
        async with self.bot.pool.acquire() as connection:
            await connection.execute(
                """INSERT INTO locale (object_id, locale) 
                VALUES ($1, $2) ON CONFLICT (object_id) DO 
                UPDATE SET locale = $2;""",
                user_id,
                locale,
            )
        current.set(locale)
        self.cache[user_id] = locale
        return True

    async def get_user(self, user_id: User.id, default: Optional[str] = None):
        cached = self.cache.get(user_id)
        if not cached is None:
            return cached

        async with self.bot.pool.acquire() as connection:
            fetched = await connection.fetchval(
                "SELECT locale FROM locale WHERE object_id = $1", user_id
            )
        locale = fetched or default
        self.cache[user_id] = locale
        return locale

    async def set_guild(self, guild_id: Guild.id, locale: str):
        async with self.bot.pool.acquire() as connection:
            await connection.execute(
                """INSERT INTO locale (object_id, locale) 
                VALUES ($1, $2) ON CONFLICT (object_id) DO 
                UPDATE SET locale = $2;""",
                guild_id,
                locale,
            )

        current.set(locale)
        self.cache[guild_id] = locale
        return True

    async def get_guild(self, guild_id: Guild.id, default: Optional[str] = None):
        cached = self.cache.get(guild_id, None)
        if cached:
            return cached

        async with self.bot.pool.acquire() as connection:
            fetched = await connection.fetchval(
                "SELECT locale FROM locale WHERE object_id = $1", guild_id
            )

        locale = fetched or default
        self.cache[guild_id] = locale
        return locale


class Locales:
    locales: Optional[List[Locale]]

    def __init__(self, locales: Optional[List[Locale]] = None) -> None:
        self.locales = locales or list()

    def add(self, locales: Union[Locale, List[Locale]]):
        if not isinstance(locales, list):
            locales = [locales]
        locales = list(filter(lambda l: l.exists, locales))
        self.locales.extend(locales)

    @property
    def all_two_letters(self) -> Dict[str, Locale]:
        return dict((locale.two_letters.lower(), locale) for locale in self.locales)

    @property
    def unique_two_letters(self) -> Dict[str, Locale]:
        return dict(
            (two, locale)
            for two, locale in self.all_two_letters.items()
            if not list(self.all_two_letters.keys()).count(two) > 1
        )

    @property
    def languages(self) -> Dict[str, Locale]:
        return dict((locale.language.lower(), locale) for locale in self.locales)

    @property
    def simples(self) -> Dict[str, Locale]:
        return dict((locale.simplified.lower(), locale) for locale in self.locales)

    @property
    def codes(self) -> Dict[str, Locale]:
        return dict((locale.locale.lower(), locale) for locale in self.locales)

    def __call__(self, locales: List[Locale]) -> None:
        self.locales = list(filter(lambda l: l.exists, locales))

    def __getitem__(self, index):
        return self.locales[index]

    def get(self, index, default=None):
        try:
            return self.locales[index]
        except IndexError:
            return default

    def __len__(self):
        return len(self.locales)

    def __iter__(self):
        return iter(self.locales)


class Locale:
    bot: ShakeBot
    locale: str
    exists = True

    def __init__(self, bot: ShakeBot, locale: str) -> None:
        self.bot = bot
        self.locale = locale
        self.__language = self.__flag = None

        localepath = join(self.bot.i18n.directory, locale, "LC_MESSAGES", "shake.po")

        po = None
        with suppress(OSError):
            po = pofile(localepath)
        if po is None:
            self.exists = False
        self.metadata = getattr(po, "metadata", {})

    @property
    def simplified(self) -> str:
        if not self.information:
            return None
        simplified: List[str] = self.information.get("simplified")
        if not bool(simplified):
            return None
        return simplified[0]

    @property
    def language(self) -> str:
        if self.__language:
            return self.__language
        if self.information:
            language = self.information.get("language")
        else:
            language = self.metadata.get("Lanugage-Team")
        self.__language = language
        return language

    @property
    def flag(self) -> str:
        if self.__flag:
            return self.__flag

        dc = EXCEPTION.get(self.locale, None)
        if not dc:
            dc = self.locale[3:].lower()
        flag = ":flag_{}:".format(dc)
        self.__flag = flag
        return flag

    @property
    def information(self) -> Optional[dict]:
        return Localization.available.get(self.locale, None)

    @property
    def specific(self) -> Optional[str]:
        if not self.information:
            return None
        return self.information.get("specific", None)

    @property
    def underscored(self) -> str:
        if self.crowdin:
            if len(self.crowdin) == 2:
                self.locale_underscored = (
                    self.crowdin.lower() + "_" + self.crowdin.upper()
                )
            else:
                self.locale_underscored = self.crowdin.replace("-", "_")
        else:
            self.locale_underscored = None

    @property
    def crowdin(self) -> str:
        lang = self.metadata.get("X_Crowdin_Language", None)
        return lang

    @property
    def authors(self) -> List[str]:
        translators = self.metadata.get("Last-Translator", None)
        return translators.split()

    @property
    def two_letters(self) -> str:
        if crw := self.crowdin:
            two = crw
        elif lang := self.metadata.get("Language", None):
            two = lang[:2]
        else:
            two = self.locale[:2]
        return two.lower()

    def __str__(self) -> str:
        return self.locale


_ = Client.use


#
############
