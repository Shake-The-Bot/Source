from ast import parse, AsyncFunctionDef, ClassDef, Expr, Call, Name, Str
from gettext import translation, NullTranslations, gettext
from discord.ext.commands._types import Check
from discord.ext.commands import check
from contextvars import ContextVar
from logging import getLogger
from os import path, getcwd
from glob import glob
from inspect import getsource
from typing import Any, Callable, TYPE_CHECKING, Optional
from discord import app_commands, Locale, User, Guild

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import ShakeContext
else:
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot

########
#

default_locale = "en-US"
domain = 'shake'
logger = getLogger('bot')
localedir = path.join(getcwd(), 'locales')
locales: frozenset[str] = frozenset(
    map(path.basename, filter(path.isdir, glob(path.join(getcwd(), "locales", "*"))),
))
########
#

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
    locale = current_locale.get()
    return gettext_translations.get(
        locale, gettext_translations[default_locale]
    ).gettext(*args, **kwargs)


def setlocale(guild: Optional[bool] = False) -> Check[Any]:
    async def predicate(ctx: ShakeContext) -> bool:
        locale = await ctx.bot.locale.get_guild_locale(ctx.guild.id) or ('en-US' if guild else (await ctx.bot.locale.get_user_locale(ctx.author.id) or 'en-US'))
        current_locale.set(locale)
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

current_locale: ContextVar[str] = ContextVar("current_locale", default="en-US")
_ = use_current_gettext
locale_doc = i18n_docstring
current_locale.set(default_locale)

available = {
    'en-US': {'language': 'English', 'simplified': ['american english', 'english'], '_': 'English (american)' }, 
    'en-GB': {'language': 'English', 'simplified': ['british english'], '_': 'English (british)'}, 
    'bg-BG': {'language': 'български', 'simplified': ['bulgarian']}, 
    'zn-CN': {'language': '中国人', 'simplified': ['chinese', 'simplified chinese'], '_': '中国人 (简化的)'}, 
    'zn-TW': {'language': '中國人', 'simplified': ['taiwanese chinese'], '_': '中國人 (傳統的)'},
    'hr-HR': {'language': 'Hrvatski', 'simplified': ['croatian']}, 
    'cs-CS': {'language': 'čeština', 'simplified': ['czech']}, 
    'da-DA': {'language': 'Dansk', 'simplified': ['danish']}, 
    'nl-NL': {'language': 'Nederlands', 'simplified': ['dutch']}, 
    'fi-FI': {'language': 'Suomalainen', 'simplified': ['finnish']}, 
    'fr-FR': {'language': 'Français', 'simplified': ['french']}, 
    'de-DE': {'language': 'Deutsch', 'simplified': ['german'], '_': 'Deutsch (Deutschland)'}, 
    'el-EL': {'language': 'Ελληνικά', 'simplified': ['greek']}, 
    'hi-HI': {'language': 'हिन्दी', 'simplified': ['hindi']}, 
    'hu-HU': {'language': 'Magyar', 'simplified': ['hungarian']}, 
    'it-IT': {'language': 'Italiano', 'simplified': ['italian']}, 
    'ja-JA': {'language': '日本', 'simplified': ['japanese']}, 
    'ko-KO': {'language': '한국어', 'simplified': ['korean']}, 
    'lt-LT': {'language': 'Lietuviškas', 'simplified': ['lithuanian']}, 
    'no-NO': {'language': 'Norsk', 'simplified': ['norwegian']}, 
    'pl-PL': {'language': 'Polska', 'simplified': ['polish']}, 
    'pt-BR': {'language': 'portugues', 'simplified': ['portuguese'], '_': 'portugues (brasil)'}, 
    'ro-RO': {'language': 'Română', 'simplified': ['romanian']}, 
    'ru-RU': {'language': 'Русский', 'simplified': ['russian']}, 
    'es-ES': {'language': 'Español', 'simplified': ['spanish']}, 
    'sv-SE': {'language': 'Svenska', 'simplified': ['swedish']}, 
    'th-TH': {'language': 'แบบไทย', 'simplified': ['thai']}, 
    'tr-TR': {'language': 'Türkçe', 'simplified': ['turkish']}, 
    'uk-RK': {'language': 'українська', 'simplified': ['ukrainian']}, 
    'vi-VI': {'language': 'Tiếng Việt', 'simplified': ['vietnamese']}, 
}



class locale():
    def __init__(self, bot) -> None:
        self.bot: ShakeBot = bot
        return None

    async def set_user_locale(self, user_id: User.id, locale: str):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """WITH insert AS (INSERT INTO locale (id) VALUES ($1) ON CONFLICT (id) DO NOTHING)
                UPDATE locale SET locale = $2 WHERE id = $1;""", user_id, locale
            )
        current_locale.set(locale)
        self.bot.locales[user_id] = locale
        return True
    
    async def get_user_locale(self, user_id: User.id):
        if self.bot.locales.get(user_id, None):
            return self.bot.locales[user_id]
        self.bot.locales[user_id] = await self.bot.pool.fetchval(
            """WITH insert AS (INSERT INTO locale (id) VALUES ($1) ON CONFLICT (id) DO NOTHING)
            SELECT locale FROM locale WHERE id=$1;""", user_id
        ) or None
        return self.bot.locales[user_id]

    async def set_guild_locale(self, guild_id: Guild.id, locale: str):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """WITH insert AS (INSERT INTO locale (id) VALUES ($1) ON CONFLICT (id) DO NOTHING)
                UPDATE locale SET locale = $2 WHERE id = $1;""", guild_id, locale
            )
        current_locale.set(locale)
        self.bot.locales[guild_id] = locale
        return True

    async def get_guild_locale(self, guild_id: Guild.id):
        if self.bot.locales.get(guild_id, None):
            return self.bot.locales[guild_id]
        self.bot.locales[guild_id] = await self.bot.pool.fetchval(
            """WITH insert AS (INSERT INTO locale (id) VALUES ($1) ON CONFLICT (id) DO NOTHING)
            SELECT locale FROM locale WHERE id=$1;""", guild_id
        ) or None
        return self.bot.locales[guild_id]
#
############