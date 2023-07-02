import re
from enum import Enum
from functools import partial
from sys import exc_info
from typing import Any, Callable, Literal, Optional, TypedDict

from discord import Guild, PartialEmoji, Thread, User
from discord.channel import *
from discord.ext.commands import Bot

from Classes.i18n import _
from Classes.useful import string
from Extensions.extensions import CATEGORYS, Categorys

__all__ = (
    "Types",
    "TextFormat",
    "Regex",
    "OneWordBatch",
    "Locale",
    "FunctionsBatch",
    "CATEGORYS",
    "Categorys",
    "AboveMesBatch",
    "AboveMeBatch",
    "CountingBatch",
    "tick",
    "Translated",
    "TracebackType",
    "ExtensionMethods",
    "UserGuild",
)


class Translated:
    ActitiyType = {
        "unknown": _("unknown"),
        "playing": _("playing"),
        "streaming": _("streaming"),
        "listening": _("listening"),
        "watching": _("watching"),
        "custom": _("custom"),
        "competing": _("competing in"),
    }


class UserGuild(Enum):
    servers = Guild
    server = User
    users = User
    user = User
    guilds = Guild
    guild = Guild


try:
    raise TypeError
except TypeError:
    tb = exc_info()[2]
    TracebackType = type(tb)
    FrameType = type(tb.tb_frame)
    tb = None
    del tb

tick: Callable[[Bot], PartialEmoji] = lambda bot: (
    str(bot.emojis.cross),
    str(bot.emojis.hook),
)


class Locale:
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
        "zh-TW": {
            "language": "中國人",
            "simplified": ["taiwanese chinese"],
            "_": "中國人 (傳統的)",
        },
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


class TextFormat(Enum):
    quote: Callable[[str], str] = lambda t: string(t, front="„", end="“", iterate=False)
    italics: Callable[[str], str] = lambda t: string(t, "_")
    bold: Callable[[str], str] = lambda t: string(t, "**")
    bolditalics: Callable[[str], str] = lambda t: string(t, "***")
    underline: Callable[[str], str] = lambda t: string(t, "__")
    underlinebold: Callable[[str], str] = lambda t: string(t, "__", "**")
    underlinebolditalics: Callable[[str], str] = lambda t: string(t, "__", "***")
    strikethrough: Callable[[str], str] = lambda t: string(t, "~~")
    codeblock: Callable[[str], str] = lambda t: string(t, "`")
    join: Callable[[Any, str], str] = lambda *args, splitter=" ": splitter.join(
        str(arg) for arg in args
    )
    codeunderline: Callable[[str], str] = lambda t: string(t, "__", "`")
    multicodeblock: Callable[[str], str] = lambda t, f=None: string(
        t, front="```" + (f + "\n" if f else ""), end="```", iterate=False
    )
    blockquotes: Callable[[str], str] = lambda t: string(t, "> ", end=False)
    hyperlink: Callable[[str, str], str] = (
        lambda t, l: "[" + str(t) + "]" + "(" + str(l) + ")"
    )
    filler: Callable[[str], str] = lambda t, spaces=0: str(t).ljust(spaces)
    multiblockquotes: Callable[[str], str] = lambda t: string(t, ">>> ", end=False)
    biggest: Callable[[str], str] = lambda t: string(t, "# ", end=False)
    bigger: Callable[[str], str] = lambda t: string(t, "## ", end=False)
    big: Callable[[str], str] = lambda t: string(t, "### ", end=False)
    spoiler: Callable[[str], str] = lambda t: string(t, "||")
    list: Callable[[str, int], str] = lambda t, indent=0: string(
        t, (" " * indent * 2) + "- ", end=False
    )


class Types(Enum):
    ValidStaticFormatTypes = Literal["webp", "jpeg", "jpg", "png"]
    ValidAssetFormatTypes = Literal["webp", "jpeg", "jpg", "png", "gif"]
    VocalGuildChannel = VoiceChannel | StageChannel
    GuildChannel = VocalGuildChannel | ForumChannel | TextChannel | Thread
    Channel = (
        VoiceChannel
        | TextChannel
        | StageChannel
        | ForumChannel
        | CategoryChannel
        | DMChannel
    )
    RtfmPage = {
        "stable": "https://discordpy.readthedocs.io/en/stable",
        "latest": "https://discordpy.readthedocs.io/en/latest",
        "python": "https://docs.python.org/3",
    }


class Regex(Enum):
    user = r"<@!?(\d+)>"
    role = r"<@&(\d+)>"
    channel = r"<#(\d+)>"
    command = r"<\/([-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32})/:(\d+)>"
    revision = re.compile(
        r"(?P<kind>V|U)(?P<version>[0-9]+)_(?P<type>bot|guild)_(?P<description>.+).sql"
    )


class ExtensionMethods(Enum):
    load = partial(Bot.load_extension)
    unload = partial(Bot.unload_extension)
    reload = partial(Bot.reload_extension)


class CountingBatch(TypedDict):
    channel_id: int
    count: int
    user_id: int
    message_id: int
    streak: int
    best: int
    goal: int
    react: bool
    used: str
    numbers: bool


class FunctionsBatch(TypedDict):
    guild_id: int
    channel_id: int
    user_id: int
    count: int
    failed: bool
    used: str


class AboveMesBatch(TypedDict):
    guild_id: int
    channel_id: int
    user_id: int
    phrase: str
    failed: bool
    used: str


class OneWordBatch(TypedDict):
    channel_id: int
    user_id: int
    message_id: int
    count: int
    words: list
    phrase: str
    react: bool
    used: str


class AboveMeBatch(TypedDict):
    channel_id: int
    user_id: int
    message_id: int
    count: int
    phrases: list
    react: bool
    used: str
