from __future__ import annotations

import inspect
import re
from ast import literal_eval
from datetime import datetime, timezone
from difflib import get_close_matches
from typing import Any, List, Literal, Optional, Self, Tuple

import parsedatetime
from dateutil.relativedelta import relativedelta
from discord import TextChannel
from discord.app_commands import AppCommand, AppCommandGroup, Command, CommandTree
from discord.ext.commands import *

from .i18n import _
from .types import Types

units = parsedatetime.pdtLocales['en_US'].units
units['minutes'].append('mins')
units['seconds'].append('secs')

__all__ = (
    "DurationDelta",
    "ValidArg",
    "ValidKwarg",
    "ValidCog",
    "CleanChannels",
    "Age",
    "Regex",
    "Slash",
)

############
#


class ValidArg:
    """Tries to convert into a valid cog"""

    async def convert(cls, ctx: Context, argument: Any) -> Tuple[str]:  # TODO
        if "=" in argument:
            return None
        return argument


class RtfmKey(Converter):
    """convert into a valid key"""

    async def convert(cls, ctx: Context, argument: Optional[str] = None) -> List[str]:
        return argument if not argument is None and argument in Types.RtfmPage.value else None


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

    async def convert(self, ctx: Context, argument: str) -> Literal["*"] | list[TextChannel]:
        if argument == "*":
            return "*"
        return [await self._channel_converter.convert(ctx, channel) for channel in argument.split()]


class DurationDelta(Converter):
    """dateutil.relativedelta.relativedelta"""

    async def convert(self, ctx: Context, argument: str) -> relativedelta:
        if not (delta := duration(argument)):
            raise errors.BadArgument(_("`{duration}` is not a valid duration string.")).format(duration=argument)

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
            raise errors.BadArgument(f"`{duration}` results in a datetime outside the supported range.")


class Regex(Converter):
    async def convert(self, ctx: Context, argument: str) -> re.Pattern:
        match = re.fullmatch(r"`(.+?)`", argument)
        if not match:
            raise errors.BadArgument(_("Regex pattern missing wrapping backticks"))
        try:
            return compile(match.group(1), re.IGNORECASE + re.DOTALL)
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
    regex = compile(
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

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
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

    discord_fmt = re.compile(r'<t:(?P<ts>[0-9]+)(?:\:?[RFfDdTt])?>')

    dt: datetime.datetime

    def __init__(self, argument: str, *, now: Optional[datetime.datetime] = None):
        match = self.human_fmt.fullmatch(argument)
        if match is None or not match.group(0):
            match = self.discord_fmt.fullmatch(argument)
            if match is not None:
                self.dt = datetime.datetime.fromtimestamp(int(match.group('ts')), tz=datetime.timezone.utc)
                return
            else:
                raise BadArgument('invalid time provided')

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
            dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

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
            raise BadArgument('this time is in the past')


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
        return any(isinstance(option, AppCommandGroup) for option in self.app_command.options)

    @property
    def is_subcommand(self) -> bool:
        return any(
            isinstance(option, AppCommandGroup) and self.command.name in option.name for option in self.app_command.options
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


class ValidCog(Converter):
    """Tries to find a matching extension and returns it

    Triggers a BadArgument error if you specify the extensions "load", "unload" or "reload",
    because they are excluded before this function
    """

    # extension: str = (ext[:-9] if ext.endswith('.__init__') else ext).split('.')[-1] # Extensions.Commands.Other.reload.__init__ -> reload
    async def convert(self, ctx: Context, argument: str) -> str:
        def validation(final: str):
            if any(_ in str(final) for _ in ["load", "unload", "reload"]):
                raise BadArgument(message=str(final) + " is not a valid module to work with")
            return final

        if command := ctx.bot.get_command(argument):
            file = inspect.getfile(command.cog.__class__).removesuffix(".py")
            path = file.split("/")
            Extensions = path.index("Extensions")
            build = path[Extensions:]
            return validation(".".join(build))

        elif argument in ctx.bot.config.client.extensions:
            return validation(argument)

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
                    return validation(matches[0])
                raise BadArgument(message="Specified module has an incorrect structure")

            extension = ".".join(build[Extensions:]) + ".__init__"

            if extension in ctx.bot.config.client.extensions:
                return validation(extension)

            elif matches := (
                [_ for _ in ctx.bot.config.client.extensions if extension in _]
                or get_close_matches(extension, ctx.bot.config.client.extensions)
            ):
                return validation(matches[0])

        else:
            shortened = [_.split(".")[-1].lower() for _ in ctx.bot.config.client.extensions]
            if argument.lower() in shortened:
                return validation(ctx.bot.config.client.extensions[shortened.index(argument)])
            elif matches := get_close_matches(argument.lower(), shortened):
                return validation(ctx.bot.config.client.extensions[shortened.index(matches[0])])

        raise BadArgument(message="Specify either the module name or the path to the module")


#
############
