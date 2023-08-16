from __future__ import annotations

import hashlib
from ast import BinOp, Expression, PyCF_ALLOW_TOP_LEVEL_AWAIT, parse
from base64 import b64encode
from collections import defaultdict, namedtuple
from collections.abc import Callable, Container, Iterable
from functools import partial
from hmac import new
from importlib import reload
from inspect import isawaitable
from logging import getLogger
from os import getcwd, listdir
from os import urandom as _urandom
from os.path import isdir, isfile
from random import choice as rchoice
from re import I
from re import compile as recom
from re import escape, findall, sub
from string import whitespace
from sys import modules
from time import time
from typing import *
from typing import Iterable
from urllib.parse import quote
from zlib import decompressobj

from aiohttp import ClientSession, ClientTimeout, StreamReader
from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement, SoupStrainer, Tag
from discord import *
from discord.ext.commands import *
from discord.ui import View

from Classes.converter import DocMarkdownConverter
from Classes.exceptions import NoDumpingSpots, NotVoted
from Classes.i18n import _
from Classes.tomls.configuration import config
from Classes.types import DocItem, Modules

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.converter import ValidExt
    from Classes.helpful import ShakeContext
    from Classes.types import ExtensionMethods


MAX_SIGNATURE_AMOUNT = 3


_NO_SIGNATURE_GROUPS = {
    "attribute",
    "envvar",
    "setting",
    "tempaltefilter",
    "markdown",
    "templatetag",
    "term",
}


BracketPair = namedtuple("BracketPair", ["opening_bracket", "closing_bracket"])
_BRACKET_PAIRS = {
    "{": BracketPair("{", "}"),
    "(": BracketPair("(", ")"),
    "[": BracketPair("[", "]"),
    "<": BracketPair("<", ">"),
}


_WHITESPACE_AFTER_NEWLINES_RE = recom(r"(?<=\n\n)(\s+)")

_EMBED_CODE_BLOCK_LINE_LENGTH = 61
_MAX_SIGNATURES_LENGTH = (_EMBED_CODE_BLOCK_LINE_LENGTH + 8) * MAX_SIGNATURE_AMOUNT
_TRUNCATE_STRIP_CHARACTERS = "!?:;." + whitespace
_MAX_DESCRIPTION_LENGTH = 4096 - _MAX_SIGNATURES_LENGTH

log = getLogger()

__all__ = (
    "human_join",
    "source_lines",
    "get_signature",
    "votecheck",
    "get_file_paths",
    "dump",
    "chunk",
    "extshandler",
    "romans",
    "decimals",
    "MISSING",
    "evaluate",
    "string_is_calculation",
    "choice",
    "getrandbits",
    "stdoutable",
    "random_token",
    "stdoutable",
    "get_dd_elements",
    "get_general_elements",
    "get_signatures",
    "truncate",
    "safe_output",
    "async_compile",
    "cleanup",
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


chunk = lambda seq, size: [seq[i : i + size] for i in range(0, len(seq), size)]

"""     Text     """

_SEARCH_END_TAG_ATTRS = (
    "data",
    "function",
    "class",
    "exception",
    "seealso",
    "section",
    "rubric",
    "sphinxsidebar",
)


class Strainer(SoupStrainer):
    """Subclass of SoupStrainer to allow matching of both `Tag`s and `NavigableString`s."""

    def __init__(self, *, include_strings: bool, **kwargs):
        self.include_strings = include_strings
        passed_text = kwargs.pop("text", None)
        if passed_text is not None:
            log.warning("`text` is not a supported kwarg in the custom strainer.")
        super().__init__(**kwargs)

    Markup = PageElement | list["Markup"]

    def search(self, markup: Markup) -> PageElement | str:
        """Extend default SoupStrainer behaviour to allow matching both `Tag`s` and `NavigableString`s."""
        if isinstance(markup, str):
            # Let everything through the text filter if we're including strings and tags.
            if not self.name and not self.attrs and self.include_strings:
                return markup
            return None
        return super().search(markup)


def _find_elements_until_tag(
    start_element: PageElement,
    end_tag_filter: Container[str] | Callable[[Tag], bool],
    *,
    func: Callable,
    include_strings: bool = False,
    limit: int | None = None,
) -> list[Tag | NavigableString]:
    """
    Get all elements up to `limit` or until a tag matching `end_tag_filter` is found.

    `end_tag_filter` can be either a container of string names to check against,
    or a filtering callable that's applied to tags.

    When `include_strings` is True, `NavigableString`s from the document will be included in the result along `Tag`s.

    `func` takes in a BeautifulSoup unbound method for finding multiple elements, such as `BeautifulSoup.find_all`.
    The method is then iterated over and all elements until the matching tag or the limit are added to the return list.
    """
    use_container_filter = not callable(end_tag_filter)
    elements = []

    for element in func(
        start_element, name=Strainer(include_strings=include_strings), limit=limit
    ):
        if isinstance(element, Tag):
            if use_container_filter:
                if element.name in end_tag_filter:
                    break
            elif end_tag_filter(element):
                break
        elements.append(element)

    return elements


_find_next_children_until_tag = partial(
    _find_elements_until_tag, func=partial(BeautifulSoup.find_all, recursive=False)
)
_find_recursive_children_until_tag = partial(
    _find_elements_until_tag, func=BeautifulSoup.find_all
)
_find_next_siblings_until_tag = partial(
    _find_elements_until_tag, func=BeautifulSoup.find_next_siblings
)
_find_previous_siblings_until_tag = partial(
    _find_elements_until_tag, func=BeautifulSoup.find_previous_siblings
)


def _class_filter_factory(class_names: Iterable[str]) -> Callable[[Tag], bool]:
    """Create callable that returns True when the passed in tag's class is in `class_names` or when it's a table."""

    def match_tag(tag: Tag) -> bool:
        for attr in class_names:
            if attr in tag.get("class", ()):
                return True
        return tag.name == "table"

    return match_tag


def get_general_elements(start_element: Tag) -> list[Tag | NavigableString]:
    """
    Get page content to a table or a tag with its class in `SEARCH_END_TAG_ATTRS`.

    A headerlink tag is attempted to be found to skip repeating the symbol information in the description.
    If it's found it's used as the tag to start the search from instead of the `start_element`.
    """
    child_tags = _find_recursive_children_until_tag(
        start_element, _class_filter_factory(["section"]), limit=100
    )
    header = next(filter(_class_filter_factory(["headerlink"]), child_tags), None)
    start_tag = header.parent if header is not None else start_element
    return _find_next_siblings_until_tag(
        start_tag, _class_filter_factory(_SEARCH_END_TAG_ATTRS), include_strings=True
    )


def get_dd_elements(symbol: PageElement) -> list[Tag | NavigableString]:
    """Get the contents of the next dd tag, up to a dt or a dl tag."""
    description_tag = symbol.find_next("dd")
    return _find_next_children_until_tag(
        description_tag, ("dt", "dl"), include_strings=True
    )


def get_signatures(start_signature: PageElement) -> list[str]:
    """
    Collect up to `_MAX_SIGNATURE_AMOUNT` signatures from dt tags around the `start_signature` dt tag.

    First the signatures under the `start_signature` are included;
    if less than 2 are found, tags above the start signature are added to the result if any are present.
    """
    signatures = []
    for element in (
        *reversed(_find_previous_siblings_until_tag(start_signature, ("dd",), limit=2)),
        start_signature,
        *_find_next_siblings_until_tag(start_signature, ("dd",), limit=2),
    )[-MAX_SIGNATURE_AMOUNT:]:
        for tag in element.find_all(_filter_signature_links, recursive=False):
            tag.decompose()

        signature = element.text
        if signature:
            signatures.append(signature)

    return signatures


def _filter_signature_links(tag: Tag) -> bool:
    """Return True if `tag` is a headerlink, or a link to source code; False otherwise."""
    if tag.name == "a":
        if "headerlink" in tag.get("class", ()):
            return True

        if tag.find(class_="viewcode-link"):
            return True

    return False


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


def evaluate(string):
    try:
        tree = parse(string, mode="eval")
        result = eval(compile(tree, filename="<string>", mode="eval"))
        return result
    except (SyntaxError, TypeError, NameError):
        return None


def decimals(string: str):
    pattern = r"[-+]?\d+\.[0-9]+(?:[eE][+-]?\d+)?"

    matches = findall(pattern, string)

    for match in matches:
        number = float(match)

        if not number < 1:
            continue

        lenght = len(str(number))
        multiplicator = int("1" + "0" * (lenght - 2))
        string = string.replace(match, str(int(float(number * multiplicator))), 1)

    return string


def romans(string: str):
    pattern = r"M{0,3}(?:CM|CD|D?C{0,3})?(?:XC|XL|L?X{0,3})?(?:IX|IV|V?I{0,3})?"
    matches = list(filter(lambda m: bool(m), findall(pattern, string)))

    for match in matches:
        values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
        result = 0
        last = 0

        for char in match[::-1]:
            digit = values[char]
            if not digit:
                continue

            if digit >= last:
                result += digit
                last = digit
            else:
                result -= digit

        if result:
            string = string.replace(match, str(result), 1)

    return string


def string_is_calculation(string):
    try:
        tree = parse(string, mode="eval")
    except SyntaxError:
        return False

    if not isinstance(tree, Expression):
        return False

    if not isinstance(tree.body, BinOp):
        return False

    return True


def files(origin: str) -> Iterator[int]:
    for following in listdir(origin):
        x: str = f"{origin}/{following}"

        if isdir(x):
            yield from files(x)

        if not isfile(x):
            continue

        if x.endswith((".py")) and not x.startswith("."):
            yield x


get_file_paths = lambda origin: list(files(origin))


def source_lines(path: Optional[str] = None) -> int:
    path = path or getcwd()

    def summed(path):
        for path in files(path):
            with open(path, encoding="utf8") as f:
                yield len(
                    [
                        line
                        for line in f.readlines()
                        if not line.strip().startswith("#") and not "import" in line
                    ]
                )

    return sum(summed(path))


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

    header = {"Authorization": config.auth.topgg.token}
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


async def extshandler(ctx: Context, extensions: list[str], method: Enum) -> None:
    extensions: List[str] = [extensions] if isinstance(extensions, str) else extensions

    async def handle(method: ExtensionMethods, extension: ValidExt) -> str:
        function = method.value
        error = None

        try:
            await function(ctx.bot, extension)

        except NoEntryPointError:
            try:
                if extension in modules.keys():
                    reload(modules[extension])
                else:
                    __import__(extension)
            except (ImportError, SyntaxError) as error:
                return error

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
    prefix = "Bearer "
    try:
        try:
            async with session.post(
                "https://hastepaste.com/api/create",
                data=f"raw=false&text={quote(content)}",
                headers={
                    "User-Agent": "Shake",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            ) as post:
                if not 200 <= post.status < 400:
                    raise
                text = await post.text()
                return text
        except:
            try:
                async with session.post(
                    "https://hastebin.com/documents",
                    data=content,
                    headers={"Authorization": prefix + config.auth.hastebin.token},
                ) as post:
                    if not 200 <= post.status < 400:
                        raise
                    text = await post.text()
                    return f"https://hastebin.com/share/{text[8:-2]}"
            except:
                try:
                    async with session.post(
                        "https://api.mystb.in/paste", data=content
                    ) as post:
                        if not 200 <= post.status < 400:
                            raise
                        return (
                            "https://mystb.in/" + (await post.json())["pastes"][0]["id"]
                        )
                except:
                    async with session.post(
                        "https://bin.readthedocs.fr/new",
                        data={"code": content, "lang": lang},
                    ) as post:
                        if not 200 <= post.status < 400:
                            raise
                        text = post.url
                        return text
    except:
        raise NoDumpingSpots("All tried hosts did not work")


def get_signature(menu: View, command: Command):
    bot: ShakeBot = menu.ctx.bot
    guild: Guild = menu.ctx.guild

    if command.usage is not None:
        return command.usage

    params = command.clean_params
    if not params:
        return {}, {}

    optionals = dict()
    required = dict()

    text_channels = list(channel.mention for channel in guild.text_channels[:2])
    members = list(member.mention for member in guild.members[:2])
    voice_channels = list(channel.mention for channel in guild.voice_channels[:2])

    examples = {
        int: [choice(range(0, 100))],
        Member: [bot.user.mention, menu.ctx.author.mention] + members,
        User: [bot.user.id],
        TextChannel: text_channels,
        VoiceChannel: voice_channels,
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

        example = examples.get(annotation, [f"{{{name}}}"])
        if hasattr(command, "examples") or hasattr(command.callback, "examples"):
            examples = getattr(
                command, "examples", getattr(command.callback, "examples", MISSING)
            )
            assert examples
            if name in examples:
                example: Dict[str, List] = examples[name]

        if not greedy and origin is Union:
            none_cls = type(None)
            union_args = annotation.__args__
            optional = union_args[-1] is none_cls
            if len(union_args) == 2 and optional:
                annotation = union_args[0]
                origin = getattr(annotation, "__origin__", None)

        if annotation is Attachment:
            if optional:
                optionals[_("[{name} (upload a file)]".format(name=name))] = example
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
                ] = example
                continue
            else:
                optionals[f"[{name}: {annotation.__name__}]"] = example
            continue

        elif param.kind == param.VAR_POSITIONAL:
            if command.require_var_positional:
                required[f"<{name}: {annotation.__name__}…>"] = str(example)
            else:
                optionals[f"[{name}: {annotation.__name__}…]"] = example
        elif optional:
            optionals[f"[{name}: {annotation.__name__}]"] = example
        else:
            if greedy:
                optionals[f"[{name}: {annotation.__name__}]…"] = example
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
    codeblocks = ("```", "``", "`")
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
    return "\u200b{0.text:>{0.offset}}{1:>{0.offset}}\n{2}: {0}".format(
        e, "^", type(e).__name__
    )


def stdoutable(code: str, output: bool = False):
    content = code.split("\n")
    s = ""
    for i, line in enumerate(content):
        s += ("..." if output else ">>>") + " "
        s += line + "\n"
    return s


class SphinxObjectFileReader:
    BUFSIZE = 16 * 1024
    stream: StreamReader

    def __init__(self, stream):
        self.stream = stream

    def readline(self) -> str:
        return self.stream.readline().decode("utf-8")

    def skipline(self) -> None:
        self.stream.readline()

    async def read_compressed_chunks(self) -> AsyncIterator[bytes]:
        decompressor = decompressobj()
        async for chunk in self.stream.iter_chunked(self.BUFSIZE):
            if len(chunk) == 0:
                break

            yield decompressor.decompress(chunk)

        yield decompressor.flush()

    def read_compressed_lines(self) -> Generator[str, None, None]:
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")

    async def __aiter__(self) -> AsyncIterator[str]:
        """Yield lines of decompressed text."""
        buf = b""
        async for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode()
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


LINE_RE = recom(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+?(\S*)\s+(.*)")


async def fetch_inventory(
    session: ClientSession, module: Modules
) -> defaultdict[str, list[DocItem]]:
    """Fetch, parse and return an intersphinx inventory file from an url."""
    timeout = ClientTimeout(sock_connect=5, sock_read=5)
    base_url = module.value
    async with session.get(
        base_url + "objects.inv", timeout=timeout, raise_for_status=True
    ) as response:
        stream = response.content

        inventory_header = (await stream.readline()).decode().rstrip()
        try:
            sphinx_version = int(inventory_header[-1:])
        except ValueError:
            raise RuntimeError("Unable to convert inventory version header.")

        projectinfo = (await stream.readline()).decode().rstrip()
        versioninfo = (await stream.readline()).decode().rstrip()

        if not projectinfo.startswith("# Project") or not versioninfo.startswith(
            "# Version"
        ):
            raise RuntimeError(
                f"Inventory on {base_url} missing project or version header."
            )

        version = versioninfo[11:]
        project = projectinfo[11:]

        invdata = defaultdict(list)
        pathdata = defaultdict(list)

        if sphinx_version == 1:
            raise RuntimeError(str(base_url) + " is version 1")

            async for line in stream:
                name, type_, location = line.decode().rstrip().split(maxsplit=2)
                # version 1 did not add anchors to the location
                if type_ == "mod":
                    type_ = "py:module"
                    location += "#module-" + name
                else:
                    type_ = "py:" + type_
                    location += "#" + name
                invdata[type_].append((name, location))

        elif sphinx_version == 2:
            if b"zlib" not in await stream.readline():
                raise RuntimeError(
                    "'zlib' not found in header of compressed inventory."
                )

            async for line in SphinxObjectFileReader(stream):
                m = LINE_RE.match(line.rstrip())

                # ignore the parsed items we don't need
                name, directive, prio, location, display_name = m.groups()

                if location.endswith("$"):
                    location = location[:-1] + name

                domain, _, subdirective = directive.partition(":")
                relative, _, id = location.partition("#")

                # if directive == "std:doc":
                #     subdirective = "label"

                if display_name == "-":
                    key = name or id
                else:
                    key = display_name

                if key.startswith(module.name + "."):
                    key = key.removeprefix(module.name + ".")

                item = DocItem(
                    id=id,
                    name=key,
                    module=module,
                    subdirective=subdirective,
                    relative=relative,
                    location=location,
                    version=version,
                )
                pathdata[relative].append(item)

        else:
            raise RuntimeError(f"Incompatible inventory version on {base_url}.")

        return pathdata


async def markdown(item: DocItem, soup: BeautifulSoup) -> str | None:
    """
    Return a parsed Markdown string with the signatures (wrapped in python codeblocks, separated from the description by a newline) at the top of the passed item using the passed in soup,
    truncated to fit within a discord message (max 750 rendered characters for the description) with signatures at the start.

    The method of parsing and what information gets included depends on the symbol's group.
    """
    heading = soup.find(id=item.id)

    if heading is None:
        return None

    signatures = None
    # Modules, doc pages and labels don't point to description list tags but to tags like divs,
    # no special parsing can be done so we only try to include what's under them.
    if heading.name != "dt":
        elements = get_general_elements(heading)

    else:
        if not item.subdirective in _NO_SIGNATURE_GROUPS:
            signatures = get_signatures(heading)
        elements = get_dd_elements(heading)

    for element in elements:
        if isinstance(element, Tag):
            for tag in element.find_all("a", class_="headerlink"):
                tag.decompose()

    converter = DocMarkdownConverter(bullets="•", page_url=item.module.value)
    description = await truncate(
        elements, converter=converter, max_length=750, max_lines=13
    )
    description = _WHITESPACE_AFTER_NEWLINES_RE.sub("", description)

    if signatures is not None:
        signature = "".join(f"```py\n{signature}```" for signature in signatures)
        description = f"{signature}\n{description}"

    return description.strip()


async def truncate(
    elements: Iterable[Tag | NavigableString],
    converter: DocMarkdownConverter,
    max_length: int,
    max_lines: int,
) -> str:
    result = ""
    # Stores indices into `result` which point to the end boundary of each Markdown element.
    ends = []
    rendered = 0

    end = 0
    for element in elements:
        is_tag = isinstance(element, Tag)
        length = len(element.text) if is_tag else len(element)

        if rendered + length >= max_length:
            break

        if is_tag:
            markdown: str = converter.process_tag(element, convert_as_inline=False)
        else:
            markdown: str = converter.process_text(element)

        rendered += length
        end += len(markdown)

        if not markdown.isspace():
            ends.append(end)

        result += markdown

    if not ends:
        return ""

    newline_truncate_index = 0
    for _ in range(max_lines):
        newline_truncate_index = result.find("\n", newline_truncate_index + 1)
        if newline_truncate_index == -1:
            newline_truncate_index = None
            break

    if (
        newline_truncate_index is not None
        and newline_truncate_index < _MAX_DESCRIPTION_LENGTH - 3
    ):
        # Truncate based on maximum lines if there are more than the maximum number of lines.
        truncate_index = newline_truncate_index
    else:
        # There are less than the maximum number of lines; truncate based on the max char length.
        truncate_index = _MAX_DESCRIPTION_LENGTH - 3

    # Nothing needs to be truncated if the last element ends before the truncation index.
    if truncate_index >= ends[-1]:
        return result

    # Determine the actual truncation index.
    possible_truncation_indices = [cut for cut in ends if cut < truncate_index]
    if not possible_truncation_indices:
        # In case there is no Markdown element ending before the truncation index, try to find a good cutoff point.
        force_truncated = result[:truncate_index]
        # If there is an incomplete codeblock, cut it out.
        if force_truncated.count("```") % 2:
            force_truncated = force_truncated[: force_truncated.rfind("```")]
        # Search for substrings to truncate at, with decreasing desirability.
        for string_ in ("\n\n", "\n", ". ", ", ", ",", " "):
            cutoff = force_truncated.rfind(string_)

            if cutoff != -1:
                truncated_result = force_truncated[:cutoff]
                break
        else:
            truncated_result = force_truncated

    else:
        # Truncate at the last Markdown element that comes before the truncation index.
        markdown_truncate_index = possible_truncation_indices[-1]
        truncated_result = result[:markdown_truncate_index]

    return truncated_result.strip(_TRUNCATE_STRIP_CHARACTERS) + "..."
