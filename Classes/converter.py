from __future__ import annotations

import inspect
import re
from ast import literal_eval
from datetime import datetime, timezone
from difflib import get_close_matches
from os import listdir, walk
from os.path import isdir, isfile
from typing import Any, Iterator, Literal, Optional, Self, Tuple
from urllib.parse import urljoin

import markdownify
import parsedatetime
from bs4.element import PageElement
from dateutil.relativedelta import relativedelta
from discord import TextChannel, Thread, abc, utils
from discord.app_commands import AppCommand, AppCommandGroup, Command, CommandTree
from discord.ext.commands import *
from discord.ext.commands.converter import _get_from_guilds
from markdownify import chomp

from Classes.i18n import _

markdownify.whitespace_re = re.compile(r"[\r\n\s\t ]+")

units = parsedatetime.pdtLocales["en_US"].units
units["minutes"].append("mins")
units["seconds"].append("secs")

__all__ = (
    "DurationDelta",
    "ValidArg",
    "ValidKwarg",
    "ValidExt",
    "GuildChannelConverter",
    "CleanChannels",
    "Age",
    "Regex",
    "Slash",
)

############
#


class DocMarkdownConverter(markdownify.MarkdownConverter):
    def __init__(self, *, page_url: str, **options):
        super().__init__(**options)
        self.page_url = page_url

    def convert_li(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Fix markdownify's erroneous indexing in ol tags."""
        parent = el.parent
        if parent is not None and parent.name == "ol":
            li_tags = parent.find_all("li")
            bullet = f"{li_tags.index(el)+1}."
        else:
            depth = -1
            while el:
                if el.name == "ul":
                    depth += 1
                el = el.parent
            bullets = self.options["bullets"]
            bullet = bullets[depth % len(bullets)]
        return f"{bullet} {text}\n"

    def convert_hn(
        self, _n: int, el: PageElement, text: str, convert_as_inline: bool
    ) -> str:
        """Convert h tags to bold text with ** instead of adding #."""
        if convert_as_inline:
            return text
        return f"**{text}**\n\n"

    def convert_code(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Undo `markdownify`s underscore escaping."""
        return f"`{text}`".replace("\\", "")

    def convert_pre(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Wrap any codeblocks in `py` for syntax highlighting."""
        code = "".join(el.strings)
        return f"```py\n{code}```\n"

    def convert_a(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Resolve relative URLs to `self.page_url`."""
        el["href"] = urljoin(self.page_url, el["href"])
        prefix, suffix, text = chomp(text)
        if not text:
            return ""
        href = el.get("href")
        title = el.get("title")
        # For the replacement see #29: text nodes underscores are escaped
        if (
            self.options["autolinks"]
            and text.replace(r"\_", "_") == href
            and not title
            and not self.options["default_title"]
        ):
            # Shortcut syntax
            return "<%s>" % href
        if self.options["default_title"] and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        "%s[%s](%s%s)%s" % (prefix, text, href, title_part, suffix) if href else text
        return super().convert_a(el, text, convert_as_inline)

    def convert_p(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Include only one newline instead of two when the parent is a li tag."""
        if convert_as_inline:
            return text

        parent = el.parent
        if parent is not None and parent.name == "li":
            return f"{text}\n"
        return super().convert_p(el, text, convert_as_inline)

    def convert_hr(self, el: PageElement, text: str, convert_as_inline: bool) -> str:
        """Ignore `hr` tag."""
        return ""


class ValidArg:
    """Tries to convert into a valid cog"""

    async def convert(cls, ctx: Context, argument: Any) -> Tuple[str]:  # TODO
        if "=" in argument:
            return None
        return argument


class ValidKwarg(Converter):
    """Tries to convert into a valid cog"""

    async def convert(cls, ctx: Context, argument: str) -> Tuple[Any]:  # TODO
        args = ()
        kwargs = dict()
        for ix, arg in enumerate(argument.split()):
            try:
                key, value = arg.split("=")
            except (TypeError, ValueError):
                args = args + (arg,)
            else:
                kwargs[key] = literal_eval(value)
        return args, kwargs


class CleanChannels(Converter):
    _channel_converter = TextChannelConverter()

    async def convert(
        self, ctx: Context, argument: str
    ) -> Literal["*"] | list[TextChannel]:
        if argument == "*":
            return "*"
        return [
            await self._channel_converter.convert(ctx, channel)
            for channel in argument.split()
        ]


class DurationDelta(Converter):
    """dateutil.relativedelta.relativedelta"""

    async def convert(self, ctx: Context, argument: str) -> relativedelta:
        if not (delta := duration(argument)):
            raise errors.BadArgument(
                _("`{duration}` is not a valid duration string.")
            ).format(duration=argument)

        return delta


class Age(DurationDelta):
    """Convert duration strings into UTC datetime.datetime objects."""

    async def convert(self, ctx: Context, duration: str) -> datetime:
        """
        Converts a `duration` string to a datetime object that's `duration` in the past.

        The converter supports the same symbols for each unit of time as its parent class.
        """
        delta = await super().convert(ctx, duration)
        now = datetime.now(timezone.utc)

        try:
            return now - delta
        except (ValueError, OverflowError):
            raise errors.BadArgument(
                f"`{duration}` results in a datetime outside the supported range."
            )


class Regex(Converter):
    async def convert(self, ctx: Context, argument: str) -> re.Pattern:
        match = re.fullmatch(r"`(.+?)`", argument)
        if not match:
            raise errors.BadArgument(_("Regex pattern missing wrapping backticks"))
        try:
            return re.compile(match.group(1), re.IGNORECASE + re.DOTALL)
        except re.error as e:
            raise errors.BadArgument(_("Regex error: {e_msg}")).format(e_msg=e.msg)


def duration(duration: str) -> Optional[relativedelta]:
    """
    Convert a `duration` string to a relativedelta object.
    The following symbols are supported for each unit of time:

    - years: `Y`, `y`, `year`, `years`
    - months: `m`, `month`, `months`
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `M`, `minute`, `minutes`
    - seconds: `S`, `s`, `second`, `seconds`

    The units need to be provided in descending order of magnitude.
    Return None if the `duration` string cannot be parsed according to the symbols above.
    """
    regex = re.compile(
        r"((?P<years>\d+?) ?(years|year|Y|y) ?)?"
        r"((?P<months>\d+?) ?(months|month|m) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|M) ?)?"
        r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
    )
    match = regex.fullmatch(duration)
    if not match:
        return None

    duration_dict = {
        unit: int(amount) for unit, amount in match.groupdict(default=0).items()
    }
    delta = relativedelta(**duration_dict)

    return delta


class ShortTime:
    human_fmt = re.compile(
        """
           (?:(?P<years>[0-9])(?:years?|year|Y|y))?             # e.g. 2y
           (?:(?P<months>[0-9]{1,2})(?:months?|month|m))?       # e.g. 2months
           (?:(?P<weeks>[0-9]{1,4})(?:weeks?|week|W|w))?        # e.g. 10w
           (?:(?P<days>[0-9]{1,5})(?:days?|day|D|d))?           # e.g. 14d
           (?:(?P<hours>[0-9]{1,5})(?:hours?|hour|H|h))?        # e.g. 12h
           (?:(?P<minutes>[0-9]{1,5})(?:minutes?|minute|M))?    # e.g. 10m
           (?:(?P<seconds>[0-9]{1,5})(?:seconds?|second|S|s))?  # e.g. 15s
        """,
        re.VERBOSE,
    )

    discord_fmt = re.compile(r"<t:(?P<ts>[0-9]+)(?:\:?[RFfDdTt])?>")

    dt: datetime.datetime

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None):
        match = self.human_fmt.fullmatch(argument)
        if match is None or not match.group(0):
            match = self.discord_fmt.fullmatch(argument)
            if match is not None:
                self.dt = datetime.datetime.fromtimestamp(
                    int(match.group("ts")), tz=datetime.timezone.utc
                )
                return
            else:
                raise BadArgument("invalid time provided")

        data = {k: int(v) for k, v in match.groupdict(default=0).items()}
        now = now or datetime.datetime.now(datetime.timezone.utc)
        self.dt = now + relativedelta(**data)

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Self:
        return cls(argument, now=ctx.message.created_at)


class HumanTime:
    calendar = parsedatetime.Calendar(version=parsedatetime.VERSION_CONTEXT_STYLE)

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None):
        now = now or datetime.datetime.utcnow()
        dt, status = self.calendar.parseDT(argument, sourceTime=now)
        if not status.hasDateOrTime:
            raise BadArgument('invalid time provided, try e.g. "tomorrow" or "3 days"')

        if not status.hasTime:
            # replace it with the current time
            dt = dt.replace(
                hour=now.hour,
                minute=now.minute,
                second=now.second,
                microsecond=now.microsecond,
            )

        self.dt: datetime.datetime = dt
        self._past: bool = dt < now

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> Self:
        return cls(argument, now=ctx.message.created_at)


class Time(HumanTime):
    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None):
        try:
            o = ShortTime(argument, now=now)
        except Exception as e:
            super().__init__(argument)
        else:
            self.dt = o.dt
            self._past = False


class FutureTime(Time):
    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None):
        super().__init__(argument, now=now)

        if self._past:
            raise BadArgument("this time is in the past")


class Slash:
    bot: Bot
    tree: CommandTree

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.tree = self.bot.tree
        self.app_command: AppCommand = None
        self.command: Command = None

    async def __await__(self, command: Command | str) -> Slash:
        command = self.bot.get_command(command) if isinstance(command, str) else command
        if command == None:
            raise ValueError("Given Command is not found.")
        self.command = command
        self.app_command = await self.get_command()
        return self

    @property
    def is_group(self) -> bool:
        return any(
            isinstance(option, AppCommandGroup) for option in self.app_command.options
        )

    @property
    def is_subcommand(self) -> bool:
        return any(
            isinstance(option, AppCommandGroup) and self.command.name in option.name
            for option in self.app_command.options
        )

    async def get_sub_command(self, sub_command: Command) -> tuple[AppCommand, str]:
        """Gets the app_command with its sub command(s) + its mention"""
        app_command = await self.get_command(sub_command.parent)

        if not self.is_group and not self.is_subcommand:
            return None

        custom_mention = f"</{app_command.name} {sub_command.name}:{app_command.id}>"
        return app_command, custom_mention

    async def get_command(self, command: Optional[AppCommand] = None) -> AppCommand:
        """Gets the AppCommand from a command (or command name)"""
        if (command := command or self.command) is None:
            raise ValueError("Argument `command` is not given/set")

        if isinstance(command, AppCommand):
            return command
        if isinstance(command, str):
            return self.bot.tree.get_command(command)
        for app_command in await self.tree.fetch_commands(guild=None):
            if command.name == app_command.name:
                return app_command
        return None


def files(origin: str) -> Iterator[int]:
    for following in listdir(origin):
        x: str = f"{origin}/{following}"

        if isdir(x):
            yield from files(x)

        if not isfile(x):
            continue

        if x.endswith((".py")) and not x.startswith("."):
            yield x


classes = list(files("Classes"))


class ValidExt(Converter):
    """Tries to find a matching extension and returns it

    Triggers a BadArgument error if you specify the extensions "load", "unload" or "reload",
    because they are excluded from this function
    """

    # extension: str = (ext[:-9] if ext.endswith('.__init__') else ext).split('.')[-1] # Extensions.Commands.Other.reload.__init__ -> reload
    async def convert(self, ctx: Context, argument: str) -> str:
        if command := ctx.bot.get_command(argument):
            file = inspect.getfile(command.cog.__class__).removesuffix(".py")
            path = file.split("/")
            Extensions = path.index("Extensions")
            build = path[Extensions:]
            return ValidExt.validation(".".join(build))

        elif "classes" in argument.lower() and (
            matches := get_close_matches(argument, classes)
        ):
            return ValidExt.validation(
                ".".join(matches[0].split("/")).removesuffix(".py")
            )

        elif argument in ctx.bot.config.client.extensions:
            return ValidExt.validation(argument)

        elif len(parts := re.split(r"[./]", argument)) > 1:
            build = list(filter(lambda x: not x in ["__init__", "py"], parts))

            try:
                Extensions = build.index("Extensions")
            except ValueError:
                fallback = ".".join(build)
                if matches := (
                    [_ for _ in ctx.bot.config.client.extensions if fallback in _]
                    or get_close_matches(fallback, ctx.bot.config.client.extensions)
                ):
                    return ValidExt.validation(matches[0])
                raise BadArgument(message="Specified module has an incorrect structure")

            extension = ".".join(build[Extensions:]) + ".__init__"

            if extension in ctx.bot.config.client.extensions:
                return ValidExt.validation(extension)

            elif matches := (
                [_ for _ in ctx.bot.config.client.extensions if extension in _]
                or get_close_matches(extension, ctx.bot.config.client.extensions)
            ):
                return ValidExt.validation(matches[0])

        else:
            shortened = [
                _.split(".")[-1].lower() for _ in ctx.bot.config.client.extensions
            ]
            if argument.lower() in shortened:
                return ValidExt.validation(
                    ctx.bot.config.client.extensions[shortened.index(argument)]
                )
            elif matches := get_close_matches(argument.lower(), shortened):
                return ValidExt.validation(
                    ctx.bot.config.client.extensions[shortened.index(matches[0])]
                )

        raise BadArgument(
            message="Specify either the module name or the path to the module"
        )

    @staticmethod
    def validation(final: str):
        if any(_ in str(final) for _ in ["load", "unload", "reload"]):
            raise BadArgument(
                message=str(final) + " is not a valid module to work with"
            )
        return final


class GuildChannelConverter(IDConverter[abc.GuildChannel | Thread]):
    """Converts to a :class:`~discord.abc.GuildChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name.

    .. versionadded:: 2.3
    """

    async def convert(self, ctx: Context, argument: str) -> abc.GuildChannel | Thread:
        return self._resolve_channel(
            ctx, argument, "channels", abc.GuildChannel | Thread
        )

    @staticmethod
    def _resolve_channel(ctx: Context, argument: str, attribute: str, type):
        bot = ctx.bot

        match = IDConverter._get_id_match(argument) or re.match(
            r"<#([0-9]{15,20})>$", argument
        )
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                iterable = getattr(guild, attribute)
                result = utils.get(iterable, name=argument)
            if not result:

                def check(c):
                    return isinstance(c, type) and c.name == argument

                result = utils.find(check, bot.get_all_channels())  # type: ignore
        else:
            channel_id = int(match.group(1))
            if guild:
                # guild.get_channel returns an explicit union instead of the base class
                result = guild.get_channel(channel_id) or guild.get_thread(channel_id)  # type: ignore
            if not result:
                result = _get_from_guilds(bot, "get_channel", channel_id)

        if not isinstance(result, type):
            raise ChannelNotFound(argument)

        return result


#
############
