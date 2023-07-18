import re
from enum import Enum
from functools import partial
from sys import exc_info
from typing import Any, Callable, List, Literal, Optional, TypedDict

from discord import Guild, PartialEmoji, Thread, User
from discord.channel import *
from discord.ext.commands import Bot

from Extensions.extensions import Categorys

__all__ = (
    "Types",
    "Format",
    "Regex",
    "OneWordBatch",
    "Localization",
    "Categorys",
    "AboveMesBatch",
    "AboveMeBatch",
    "CountingBatch",
    "tick",
    "Translated",
    "CountingsBatch",
    "AboveMesBatch",
    "Batch",
    "TracebackType",
    "ExtensionMethods",
    "UserGuild",
)


class Translated:
    ...


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


class Localization:
    available = {
        "ar-SA": {"language": "عربي", "simplified": ["arabic"]},
        "bg-BG": {"language": "български", "simplified": ["bulgarian"]},
        "cs-CZ": {"language": "čeština", "simplified": ["czech"]},
        "da-DK": {"language": "Dansk", "simplified": ["danish"]},
        "de-DE": {
            "language": "Deutsch",
            "simplified": ["german"],
            "specific": "Deutsch (Deutsch)",
        },
        "en-US": {
            "language": "English",
            "simplified": ["american english", "english"],
            "specific": "English (american)",
        },
        "en-GB": {
            "language": "English",
            "simplified": ["british english"],
            "specific": "English (british)",
        },
        "zh-CN": {
            "language": "中国人",
            "simplified": ["chinese", "simplified chinese"],
            "specific": "中国人 (简化的)",
        },
        "zh-TW": {
            "language": "中國人",
            "simplified": ["taiwanese chinese"],
            "specific": "中國人 (傳統的)",
        },
        "hr-HR": {"language": "Hrvatski", "simplified": ["croatian"]},
        "nl-NL": {"language": "Nederlands", "simplified": ["dutch"]},
        "fi-FI": {"language": "Suomalainen", "simplified": ["finnish"]},
        "fr-FR": {"language": "Français", "simplified": ["french"]},
        "el-GR": {"language": "Ελληνικά", "simplified": ["greek"]},
        "hi-IN": {"language": "हिन्दी", "simplified": ["hindi"]},
        "hu-HU": {"language": "Magyar", "simplified": ["hungarian"]},
        "it-IT": {"language": "Italiano", "simplified": ["italian"]},
        "ja-JP": {"language": "日本", "simplified": ["japanese"]},
        "ko-KR": {"language": "한국어", "simplified": ["korean"]},
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
        "uk-UA": {"language": "українська", "simplified": ["ukrainian"]},
        "vi-VN": {"language": "Tiếng Việt", "simplified": ["vietnamese"]},
    }


def string(
    text: str,
    *format: str,
    front: Optional[List[str] | bool] = None,
    end: Optional[List[str] | bool] = None,
    iterate: bool = True,
):
    front = (
        ""
        if front is False
        else "".join(front)
        if not iterate and front
        else "".join(format)
    )
    end = (
        ""
        if end is False
        else "".join(end)
        if not iterate and end
        else "".join(reversed(format))
    )
    return f"{front}{str(text)}{end}"


class Format(Enum):
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
    Manuals = {
        "stable": {
            "name": "Discord.py",
            "url": "https://discordpy.readthedocs.io/en/stable",
            "icon": "https://camo.githubusercontent.com/794a85b742b67a4ebadd1f7aae03a54b2fb2c4bd785b4c6e5bf548f6fc4a53a4/68747470733a2f2f692e696d6775722e636f6d2f5250727737306e2e6a7067",
        },
        "latest": {
            "name": "Discord.py (latest)",
            "url": "https://discordpy.readthedocs.io/en/latest",
            "icon": "https://camo.githubusercontent.com/794a85b742b67a4ebadd1f7aae03a54b2fb2c4bd785b4c6e5bf548f6fc4a53a4/68747470733a2f2f692e696d6775722e636f6d2f5250727737306e2e6a7067",
        },
        "python": {
            "url": "https://docs.python.org/3",
            "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/240px-Python-logo-notext.svg.png",
        },
        "peps": {"name": "Python peps", "url": "https://peps.python.org/"},
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


class OneWordBatch(TypedDict):
    channel_id: int
    user_id: int
    message_id: int
    words: list
    phrase: str
    react: bool
    used: str


class CountingBatch(TypedDict):
    channel_id: int
    count: int
    user_id: int
    message_id: int
    webhook: Optional[str]
    streak: int
    best: int
    goal: int
    done: bool
    direction: bool
    math: bool
    react: bool
    used: str
    numbers: bool


class AboveMeBatch(TypedDict):
    channel_id: int
    user_id: int
    message_id: int
    count: int
    phrases: list
    react: bool
    used: str


class Batch(TypedDict):
    guild_id: int
    channel_id: int
    user_id: int
    failed: bool
    used: str


class CountingsBatch(Batch):
    count: int
    direction: bool


class AboveMesBatch(Batch):
    phrase: str
