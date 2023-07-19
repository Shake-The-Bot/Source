from __future__ import annotations

from contextlib import suppress
from contextvars import ContextVar
from gettext import NullTranslations, gettext, translation
from glob import glob
from os import getcwd, path, walk
from subprocess import call
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from discord import Guild, User
from polib import pofile

from Classes.types import Localization

if TYPE_CHECKING:
    from bot import ShakeBot

__all__ = ("Client", "_", "current", "default", "translations", "Locale")
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
        self.directory = path.join(getcwd(), directory)
        self.default = default
        self.bot = bot
        bot.cache.setdefault("locales", dict())
        self.cache: Dict = bot.cache["locales"]
        self.domain = domain
        self.translate()
        self.create()

    def __call__(self) -> None:
        self.translate()
        self.create()

    @property
    def locales(
        self,
    ) -> frozenset[str]:
        return frozenset(
            map(
                path.basename,
                filter(path.isdir, glob(path.join(getcwd(), self.directory, "*"))),
            )
        ) | {self.default}

    def create(self) -> list[tuple[str, str]]:
        data_files = []
        po_dirs = [self.directory + "/" + l + "/LC_MESSAGES/" for l in self.locales]
        for d in po_dirs:
            mo_files = []
            po_files = [f for f in next(walk(d))[2] if path.splitext(f)[1] == ".po"]
            for po_file in po_files:
                filename, extension = path.splitext(po_file)
                mo_file = filename + ".mo"
                msgfmt_cmd = "msgfmt {} -o {}".format(d + po_file, d + mo_file)
                call(msgfmt_cmd, shell=True)
                mo_files.append(d + mo_file)
            data_files.append((d, mo_files))
        return data_files

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
        cached = self.cache.get(user_id, None)
        if cached:
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


class Locale:
    bot: ShakeBot
    locale: str
    exists = True

    def __init__(self, bot: ShakeBot, locale: str) -> None:
        self.bot = bot
        self.locale = locale
        self.__language = self.__flag = None

        localepath = path.join(
            self.bot.i18n.directory, locale, "LC_MESSAGES", "shake.po"
        )

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
    def language(self) -> Optional[str]:
        if self.__language:
            return self.__language
        if self.information:
            language = self.information.get("language", None)
        else:
            language = self.metadata.get("Lanugage-Team", None)
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
        two = self.metadata.get("Language", None)
        if two is None:
            two = self.crowdin[:2] if self.crowdin else self.locale[:2]
        return two.lower()

    def __str__(self) -> str:
        return self.locale


_ = Client.use


#
############
