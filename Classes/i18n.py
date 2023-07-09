from __future__ import annotations

from contextvars import ContextVar
from gettext import NullTranslations, gettext, translation
from glob import glob
from os import getcwd, path, walk
from subprocess import call
from typing import TYPE_CHECKING, Any, Dict, Optional

from discord import Guild, User

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import DatabaseProtocol

__all__ = ("Locale", "Client", "_", "current", "default", "translations")
########
#
default: str = "en-US"
translations = dict()


class Client:
    default: str
    domain: str

    def __init__(self, domain: str = "shake", directory: str = "Locales") -> None:
        self.directory = path.join(getcwd(), directory)
        self.default = default
        self.domain = domain
        self.translate()
        self.create()
        pass

    @property
    def translations(self) -> dict:
        return translations

    @property
    def locales(
        self,
    ) -> frozenset[str]:
        return frozenset(
            map(
                path.basename,
                filter(path.isdir, glob(path.join(getcwd(), "Locales", "*"))),
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
        translations = {
            locale: translation(
                self.domain,
                languages=(locale,),
                localedir=self.directory,
                fallback=True,
            )
            for locale in self.locales
        }

        translations[default] = NullTranslations()

    @staticmethod
    def use(*args: Any, **kwargs: Any) -> str:
        if not translations:
            return gettext(*args, **kwargs)
        locale = current.get()
        return translations.get(locale, translations[default]).gettext(*args, **kwargs)


current: ContextVar[str] = ContextVar("current", default=default)
_ = Client.use
current.set(default)


class Locale:
    bot: ShakeBot
    pool: DatabaseProtocol

    def __init__(self, bot) -> None:
        self.bot = bot
        self.cache: Dict = bot.cache
        self.pool = bot.pool
        pass

    async def set_user_locale(self, user_id: User.id, locale: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """INSERT INTO locale (object_id, locale) 
                VALUES ($1, $2) ON CONFLICT (object_id) DO 
                UPDATE SET locale = $2;""",
                user_id,
                locale,
            )
        current.set(locale)
        self.cache["locales"][user_id] = locale
        return True

    async def get_user_locale(self, user_id: User.id, default: Optional[str] = None):
        if self.cache["locales"].get(user_id, None):
            return self.cache["locales"][user_id]

        async with self.pool.acquire() as connection:
            value = (
                await connection.fetchval(
                    """INSERT INTO locale (object_id) VALUES ($1) ON CONFLICT (object_id) DO NOTHING
                    RETURNING locale;""",
                    user_id,
                )
                or None
            )
        self.cache["locales"][user_id] = value
        return self.cache["locales"][user_id] or default

    async def set_guild_locale(self, guild_id: Guild.id, locale: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """INSERT INTO locale (object_id, locale) 
                VALUES ($1, $2) ON CONFLICT (object_id) DO 
                UPDATE SET locale = $2;""",
                guild_id,
                locale,
            )
        current.set(locale)
        self.cache["locales"][guild_id] = locale
        return True

    async def get_guild_locale(self, guild_id: Guild.id, default: Optional[str] = None):
        if self.cache["locales"].get(guild_id, None):
            return self.cache["locales"][guild_id]
        async with self.pool.acquire() as connection:
            value = (
                await connection.fetchval(
                    """INSERT INTO locale (object_id) VALUES ($1) ON CONFLICT (object_id) DO NOTHING
                    RETURNING locale;""",
                    guild_id,
                )
                or None
            )
        self.cache["locales"][guild_id] = value
        return self.cache["locales"][guild_id] or default


#
############
