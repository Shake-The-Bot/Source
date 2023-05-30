from ast import AsyncFunctionDef, Call, ClassDef, Expr, Name, Str, parse
from contextvars import ContextVar
from gettext import NullTranslations, gettext, translation
from glob import glob
from inspect import getsource
from os import getcwd, path, walk
from subprocess import call
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from discord import Guild, User
from discord.ext.commands import check
from discord.ext.commands._types import Check

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes import DatabaseProtocol, ShakeContext
else:
    from asyncpg import Connection as DatabaseProtocol
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext

__all__ = (
    "Locale",
    "available",
    "locale_doc",
    "mo",
    "localedir",
    "locales",
    "_",
    "current",
    "setlocale",
    "default_locale",
    "gettext_translations",
)
########
#

default_locale = "en-US"
domain = "shake"
localedir = path.join(getcwd(), "Locales")
locales: frozenset[str] = frozenset(
    map(
        path.basename,
        filter(path.isdir, glob(path.join(getcwd(), "Locales", "*"))),
    )
)


def mo():
    data_files = []
    po_dirs = [localedir + "/" + l + "/LC_MESSAGES/" for l in locales]
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


def set_gettext():
    global gettext_translations
    gettext_translations = {
        locale: translation(
            domain, languages=(locale,), localedir=localedir, fallback=True
        )
        for locale in locales
    }


set_gettext()
gettext_translations["en-US"] = NullTranslations()
locales = locales | {"en-US"}


def use_current_gettext(*args: Any, **kwargs: Any) -> str:
    if not gettext_translations:
        return gettext(*args, **kwargs)
    locale = current.get()
    return gettext_translations.get(
        locale, gettext_translations[default_locale]
    ).gettext(*args, **kwargs)


def setlocale(guild: Optional[bool] = False) -> Check[Any]:
    async def predicate(ctx: ShakeContext) -> bool:
        locale = await ctx.bot.locale.get_guild_locale(ctx.guild.id) or (
            "en-US"
            if guild
            else (await ctx.bot.locale.get_user_locale(ctx.author.id) or "en-US")
        )
        current.set(locale)
        return True

    return check(predicate)


def i18n_docstring(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    src = getsource(func)
    try:
        parsed_tree = parse(src)
    except IndentationError:
        parsed_tree = parse("class Foo:\n" + src)
        assert isinstance(parsed_tree.body[0], ClassDef)
        function_body: ClassDef = parsed_tree.body[0]
        assert isinstance(function_body.body[0], AsyncFunctionDef)
        tree: AsyncFunctionDef = function_body.body[0]
    else:
        assert isinstance(parsed_tree.body[0], AsyncFunctionDef)
        tree = parsed_tree.body[0]

    if not isinstance(tree.body[0], Expr):
        return func

    gettext_call = tree.body[0].value
    if not isinstance(gettext_call, Call):
        return func

    if not isinstance(gettext_call.func, Name) or gettext_call.func.id != "_":
        return func

    assert len(gettext_call.args) == 1
    assert isinstance(gettext_call.args[0], Str)

    func.__doc__ = gettext_call.args[0].s
    return func


current: ContextVar[str] = ContextVar("current", default="en-US")
_ = use_current_gettext
locale_doc = i18n_docstring
current.set(default_locale)

available = {
    "en-US": {
        "language": "English",
        "simplified": ["american english", "english"],
        "_": "English (american)",
    },
    "en-GB": {
        "language": "English",
        "simplified": ["british english"],
        "_": "English (british)",
    },
    "bg-BG": {"language": "български", "simplified": ["bulgarian"]},
    "zh-CN": {
        "language": "中国人",
        "simplified": ["chinese", "simplified chinese"],
        "_": "中国人 (简化的)",
    },
    "zh-TW": {"language": "中國人", "simplified": ["taiwanese chinese"], "_": "中國人 (傳統的)"},
    "hr-HR": {"language": "Hrvatski", "simplified": ["croatian"]},
    "cs-CS": {"language": "čeština", "simplified": ["czech"]},
    "da-DA": {"language": "Dansk", "simplified": ["danish"]},
    "nl-NL": {"language": "Nederlands", "simplified": ["dutch"]},
    "fi-FI": {"language": "Suomalainen", "simplified": ["finnish"]},
    "fr-FR": {"language": "Français", "simplified": ["french"]},
    "de-DE": {
        "language": "Deutsch",
        "simplified": ["german"],
        "_": "Deutsch (Deutschland)",
    },
    "el-EL": {"language": "Ελληνικά", "simplified": ["greek"]},
    "hi-HI": {"language": "हिन्दी", "simplified": ["hindi"]},
    "hu-HU": {"language": "Magyar", "simplified": ["hungarian"]},
    "it-IT": {"language": "Italiano", "simplified": ["italian"]},
    "ja-JA": {"language": "日本", "simplified": ["japanese"]},
    "ko-KO": {"language": "한국어", "simplified": ["korean"]},
    "lt-LT": {"language": "Lietuviškas", "simplified": ["lithuanian"]},
    "no-NO": {"language": "Norsk", "simplified": ["norwegian"]},
    "pl-PL": {"language": "Polska", "simplified": ["polish"]},
    "pt-BR": {
        "language": "portugues",
        "simplified": ["portuguese"],
        "_": "portugues (brasil)",
    },
    "ro-RO": {"language": "Română", "simplified": ["romanian"]},
    "ru-RU": {"language": "Русский", "simplified": ["russian"]},
    "es-ES": {"language": "Español", "simplified": ["spanish"]},
    "sv-SE": {"language": "Svenska", "simplified": ["swedish"]},
    "th-TH": {"language": "แบบไทย", "simplified": ["thai"]},
    "tr-TR": {"language": "Türkçe", "simplified": ["turkish"]},
    "uk-RK": {"language": "українська", "simplified": ["ukrainian"]},
    "vi-VI": {"language": "Tiếng Việt", "simplified": ["vietnamese"]},
}


class Locale:
    def __init__(self, bot: ShakeBot) -> None:
        self.cache: Dict = bot.cache
        self.pool: DatabaseProtocol = bot.pool
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

    async def get_user_locale(self, user_id: User.id):
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
        return self.cache["locales"][user_id]

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

    async def get_guild_locale(self, guild_id: Guild.id):
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
        return self.cache["locales"][guild_id]


#
############
