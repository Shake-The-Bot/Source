from __future__ import annotations

import hashlib
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT
from base64 import b64encode
from hmac import new
from inspect import isawaitable
from math import ceil
from os import getcwd, listdir
from os import urandom as _urandom
from os.path import isdir, isfile
from random import choice as rchoice
from re import I, escape, sub
from time import time
from typing import *
from typing import Any
from urllib.parse import quote

from aiohttp import ClientSession
from discord import *
from discord.ext.commands import *
from discord.ui import View

from Classes.exceptions import NoDumpingSpots, NotVoted
from Classes.i18n import _
from Classes.tomls import config

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.converter import ValidCog
    from Classes.helpful import ShakeContext
    from Classes.types import ExtensionMethods

__all__ = (
    "human_join",
    "source_lines",
    "get_signature",
    "votecheck",
    "dump",
    "cogshandler",
    "MISSING",
    "choice",
    "getrandbits",
    "stdoutable",
    "random_token",
    "stdoutable",
    "safe_output",
    "async_compile",
    "cleanup",
    "tens",
    "maybe_await",
    "get_syntax_error",
)


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __str__(self) -> str:
        return ""

    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()


"""     Sequence    """


def choice(seq):
    """Choose a random element from a non-empty sequence.
    if an empty sequence is given, None is returned"""
    # raises IndexError if seq is empty
    if len(seq) == 0:
        return None
    else:
        return rchoice(seq)


def human_join(
    seq: Sequence[str],
    delimiter: str = ", ",
    final: Literal["or", "and"] = "and",
    joke: bool = False,
) -> str:
    if joke:
        return ""

    _("or")
    _("and")  # „Just in case gettext gets this“

    if len(seq) == 0:
        return ""

    elif len(seq) == 1:
        return seq[0]

    elif len(seq) == 2:
        return " ".join([seq[0], final, seq[1]])

    else:
        return delimiter.join(seq[:-1]) + f" {final} {seq[-1]}"


"""     Text     """


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


# outdated
def high_level_function():
    with open("...") as mfile:  # loop for files
        paths = mfile.read().splitlines()
        for path in paths:
            with open(f"{path}", "r+") as file:
                lines = file.read().splitlines()
                newlines = lines.copy()
                done = 0
                for idx, line in enumerate(lines):
                    if "@" in line and (".group" in line or ".command" in line):
                        newlines.insert(idx + 1, "    @locale_doc")
                        done += 1
                file.seek(0)
                file.write("\n".join(newlines))
                file.truncate()


"""     Numbers     """


def source_lines(path: Optional[str] = None) -> int:
    path = path or getcwd()

    def _iterate_source_line_counts(_path: str) -> Iterator[int]:
        for file in listdir(_path):
            __path: str = f"{_path}/{file}"

            if isdir(__path):
                yield from _iterate_source_line_counts(__path)

            if not isfile(__path):
                continue

            if file.endswith((".py")) and not file.startswith("."):
                with open(__path, encoding="utf8") as f:
                    yield len(
                        [
                            line
                            for line in f.readlines()
                            if not line.strip().startswith("#") and not "import" in line
                        ]
                    )

    return sum(_iterate_source_line_counts(path))


def calc(expression):
    try:
        result = eval(expression)
    # division by zero
    except ZeroDivisionError:
        result = "Undefined (division by zero)"
    # invalid expressions
    except:
        result = "Invalid expression"
    return result


"""     Others      """


async def votecheck(ctx: Optional[Context | Interaction] = MISSING):
    user: Member = getattr(ctx, "author", getattr(ctx, "user", MISSING))
    bot: ShakeBot = getattr(ctx, "bot", getattr(ctx, "client", MISSING))

    header = {"Authorization": config.other.topgg.token}
    params = {"userId": user.id}

    async with bot.session as session:
        try:
            response = await session.get(
                f"https://top.gg/api/bots/{bot.id}/check", headers=header, params=params
            )
            data = await response.json(content_type=None)

            if data["voted"] == 1:
                return True
            NotVoted()
        except:
            raise


async def cogshandler(ctx: Context, extensions: list[str], method: Enum) -> None:
    extensions: List[str] = [extensions] if isinstance(extensions, str) else extensions

    async def handle(method: ExtensionMethods, extension: ValidCog) -> str:
        function = method.value
        error = None

        try:
            await function(ctx.bot, extension)

        except ExtensionNotLoaded as error:
            if method is method.reload:
                func = await handle(method.load, extension)
                return func
            if method is method.unload:
                return None
            return error

        except (ExtensionAlreadyLoaded,) as error:
            if method is method.load:
                return None
            return error

        except Exception as err:
            return err

        return None

    return {extension: await handle(method, extension) for extension in extensions}


async def dump(
    content: str, session: ClientSession, lang: Optional[str] = "txt"
) -> Optional[str]:
    async with session.post(
        "https://hastebin.com/documents",
        data=content,
        headers={"Authorization": config.other.hastebin.token},
    ) as post:
        if 200 <= post.status < 400:
            text = await post.text()
            return f"https://hastebin.com/share/{text[8:-2]}"

    async with session.post(
        "https://hastepaste.com/api/create",
        data=f"raw=false&text={quote(content)}",
        headers={
            "User-Agent": "Shake",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ) as post:
        if 200 <= post.status < 400:
            text = await post.text()
            return text

    async with session.post("https://api.mystb.in/paste", data=content) as post:
        if 200 <= post.status < 400:
            return "https://mystb.in/" + (await post.json())["pastes"][0]["id"]

    async with session.post(
        "https://bin.readthedocs.fr/new", data={"code": content, "lang": lang}
    ) as post:
        if 200 <= post.status < 400:
            text = post.url
            return text

    raise NoDumpingSpots("All tried hosts did not work")


def get_signature(menu: View, self: Command):
    bot: ShakeBot = menu.ctx.bot
    ctx: ShakeContext = menu.ctx
    guild: Guild = menu.ctx.guild

    if self.usage is not None:
        return self.usage

    params = self.clean_params
    if not params:
        return {}, {}

    optionals = dict()
    required = dict()

    all_text_channel = {
        str(channel.name): channel.mention for channel in guild.text_channels
    }
    text_channel = (
        all_text_channel.get(
            sorted(set(all_text_channel.keys()), key=len, reverse=False)[0]
        )
        if bool(guild.text_channels)
        else None
    )

    all_members = {str(member.name): member.mention for member in guild.members}
    member = (
        all_members.get(sorted(set(all_members.keys()), key=len, reverse=False)[0])
        if bool(guild.members)
        else None
    )

    all_voice_channel = {
        str(channel.name): channel.mention for channel in guild.voice_channels
    }
    voice_channel = (
        all_voice_channel.get(
            sorted(set(all_voice_channel.keys()), key=len, reverse=False)[0]
        )
        if bool(guild.voice_channels)
        else None
    )

    examples = {
        int: [choice(range(0, 100))],
        Member: [bot.user.mention, menu.ctx.author.mention, member],
        User: [bot.user.mention],
        TextChannel: [ctx.channel.mention if ctx.channel else None, text_channel],
        VoiceChannel: [voice_channel],
        Object: [guild.id],
        Message: [menu.ctx.message.id, menu.message.id if menu.message else None],
        str: ["abc", "hello", "xyz"],
        bool: ["True", "False"],
    }
    for name, param in params.items():
        greedy = isinstance(param.converter, Greedy)
        typin = get_origin(param.converter) == Union and get_args(param.converter)[
            -1
        ] == type(None)
        optional = False  # postpone evaluation of if it's an optional argument

        if greedy:
            annotation = param.converter.converter
        elif typin:
            args = list(get_args(param.converter))
            del args[-1]
            annotation = choice(args)
        else:
            annotation = param.converter

        origin = getattr(annotation, "__origin__", None)
        example = choice(examples.get(annotation, [f"{{{name}}}"])) or f"{{{name}}}"

        if not greedy and origin is Union:
            none_cls = type(None)
            union_args = annotation.__args__
            optional = union_args[-1] is none_cls
            if len(union_args) == 2 and optional:
                annotation = union_args[0]
                origin = getattr(annotation, "__origin__", None)

        if annotation is Attachment:
            if optional:
                optionals[_("[{name} (upload a file)]".format(name=name))] = str(
                    example
                )
            else:
                required[
                    (
                        _("<{name} (upload a file)>")
                        if not greedy
                        else _("[{name} (upload files)]…")
                    ).format(name=name)
                ] = str(example)
            continue

        if origin is Literal:
            name = "|".join(
                f'"{v}"' if isinstance(v, str) else str(v) for v in annotation.__args__
            )

        if not param.required:
            if param.displayed_default:
                optionals[
                    f"[{name}: {annotation.__name__}]…"
                    if greedy
                    else f"[{name}: {annotation.__name__}]"
                ] = str(example)
                continue
            else:
                optionals[f"[{name}: {annotation.__name__}]"] = str(example)
            continue

        elif param.kind == param.VAR_POSITIONAL:
            if self.require_var_positional:
                required[f"<{name}: {annotation.__name__}…>"] = str(example)
            else:
                optionals[f"[{name}: {annotation.__name__}…]"] = str(example)
        elif optional:
            optionals[f"[{name}: {annotation.__name__}]"] = str(example)
        else:
            if greedy:
                optionals[f"[{name}: {annotation.__name__}]…"] = str(example)
            else:
                required[f"<{name}: {annotation.__name__}>"] = str(example)

    return required, optionals


def getrandbits(k):
    if k < 0:
        raise ValueError("number of bits must be non-negative")
    numbytes = (k + 7) // 8  # bits / 8 and rounded up
    x = int.from_bytes(_urandom(numbytes), "big")
    return x >> (numbytes * 8 - k)


def random_token(author):
    id_ = b64encode(str(author).encode()).decode()
    time_ = b64encode(int.to_bytes(int(time()), 6, byteorder="big")).decode()
    randbytes = bytearray(getrandbits(8) for _ in range(10))
    hmac_ = new(randbytes, randbytes, hashlib.md5).hexdigest()
    return f"{id_}.{time_}.{hmac_}"


def stdoutable(code: str, output: bool = False):
    content = code.split("\n")
    s = ""
    for i, line in enumerate(content):
        s += ("..." if output else ">>>") + " "
        s += line + "\n"
    return s


def safe_output(ctx: ShakeContext, input: str) -> str:
    """Hides the bot's token from a string."""
    token = ctx.bot.http.token
    input = input.replace("@everyone", "@\u200beveryone").replace(
        "@here", "@\u200bhere"
    )
    return sub(escape(token), random_token(ctx.author.id), input, I)


def async_compile(source, filename, mode):
    return compile(source, filename, mode, flags=PyCF_ALLOW_TOP_LEVEL_AWAIT, optimize=0)


def cleanup(content: str) -> str:
    """Automatically removes code blocks from the code."""
    starts = ("py", "js")
    for start in starts:
        if content.startswith(f"```{start}"):
            i = len(start)
            content = content[3 + i :]
    if content.startswith("```"):
        content = content[-3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip("`").strip()
    content = "\n".join(_ for _ in content.split("\n") if not _.startswith("#"))
    return content


async def maybe_await(coro):
    for i in range(2):
        if isawaitable(coro):
            coro = await coro
        else:
            return coro
    return coro


def get_syntax_error(e):
    """Format a syntax error to send to the user.

    Returns a string representation of the error formatted as a codeblock.
    """
    if e.text is None:
        return "{0.__class__.__name__}: {0}".format(e)
    return "{0.text}{1:>{0.offset}}\n{2}: {0}".format(e, "^", type(e).__name__)


def stdoutable(code: str, output: bool = False):
    content = code.split("\n")
    s = ""
    for i, line in enumerate(content):
        s += ("..." if output else ">>>") + " "
        s += line + "\n"
    return s


def tens(count: int, higher_when_same: bool = False):
    __len = len(str(count))
    __digits: List[str] = [int(_) for _ in str(count)]
    __saves = max(1, ceil(__len / 2))
    __saved = __digits[0:__saves]
    __zeros = list("0" for _ in range(len(__digits[__saves:__len])))

    final = int("".join(str(x) for x in __saved + __zeros))

    if final == count and higher_when_same:
        final += 1

    return max(1, final)
