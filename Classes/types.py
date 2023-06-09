import re
from enum import Enum
from functools import partial
from sys import exc_info
from typing import Callable, Literal, TypedDict

from discord import PartialEmoji, Thread
from discord.channel import *
from discord.ext.commands import Bot

from Classes.useful import string

__all__ = (
    "Types",
    "TextFormat",
    "Regex",
    "Categorys",
    "CATEGORYS",
    "Locale",
    "AboveMeBatch",
    "CountingBatch",
    "tick",
    "TracebackType",
    "ExtensionMethods",
)

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


class Locale(Enum):
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
    italics: Callable[[str], str] = lambda t: string(t, "_")
    bold: Callable[[str], str] = lambda t: string(t, "**")
    bolditalics: Callable[[str], str] = lambda t: string(t, "***")
    underline: Callable[[str], str] = lambda t: string(t, "__")
    underlinebold: Callable[[str], str] = lambda t: string(t, "__", "**")
    underlinebolditalics: Callable[[str], str] = lambda t: string(t, "__", "***")
    strikethrough: Callable[[str], str] = lambda t: string(t, "~~")
    codeblock: Callable[[str], str] = lambda t: string(t, "`")
    codeunderline: Callable[[str], str] = lambda t: string(t, "__", "`")
    multicodeblock: Callable[[str], str] = lambda t, f=None: string(
        t, front="```" + (f + "\n" if f else ""), end="```", iterate=False
    )
    blockquotes: Callable[[str], str] = lambda t: string(t, "> ", end=False)
    hyperlink: Callable[[str, str], str] = (
        lambda t, l: "[" + str(t) + "]" + "(" + str(l) + ")"
    )
    multiblockquotes: Callable[[str], str] = lambda t: string(t, ">>> ", end=False)
    biggest: Callable[[str], str] = lambda t: string(t, "# ", end=False)
    bigger: Callable[[str], str] = lambda t: string(t, "## ", end=False)
    big: Callable[[str], str] = lambda t: string(t, "### ", end=False)
    spoiler: Callable[[str], str] = lambda t: string(t, "||")
    list: Callable[[str, int], str] = lambda t, indent=1: string(
        t, (" " * indent * 2) + "-", end=False
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


class Categorys(Enum):
    games = partial(Bot.get_cog, "Games")
    gimmicks = partial(Bot.get_cog, "Gimmicks")
    information = partial(Bot.get_cog, "Information")
    moderation = partial(Bot.get_cog, "Moderation")
    other = partial(Bot.get_cog, "Other")


CATEGORYS = Literal[
    "Games",
    "Gimmicks",
    "Information",
    "Moderation",
    "Other",
]


class ExtensionMethods(Enum):
    load = partial(Bot.load_extension)
    unload = partial(Bot.unload_extension)
    reload = partial(Bot.reload_extension)


class CountingBatch(TypedDict):
    channel_id: int
    count: int
    user_id: int
    streak: int
    best: int
    goal: int
    used: str
    numbers: bool


class AboveMeBatch(TypedDict):
    channel_id: int
    user_id: int
    count: int
    phrases: list
    used: str
