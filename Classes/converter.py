############
#
from __future__ import annotations
from ast import literal_eval
from difflib import get_close_matches
from typing import Union, Literal, Any, Tuple, TYPE_CHECKING, Optional, List
from re import error, fullmatch, DOTALL, IGNORECASE, Pattern, compile, split
from dateutil.relativedelta import relativedelta
from discord import TextChannel, Guild
from discord.app_commands import AppCommand, AppCommandGroup, CommandTree, Command
import inspect
from discord.ext import commands
from discord.ext.commands import Context, Converter, TextChannelConverter, errors, BadArgument
from datetime import datetime, timezone

if TYPE_CHECKING:
    from Classes import _, MISSING
    from .helpful import ShakeContext, ShakeBot
    from .useful import Duration, RTFM_PAGE_TYPES

__all__ = (
    'DurationDelta', 'ValidArg', 'ValidKwarg', 'ValidCog', 
    'CleanChannels', 'Age', 'Regex', 'Slash'
)

class ValidArg():
    """Tries to convert into a valid cog"""
    
    async def convert(cls, ctx: ShakeContext, argument: Any) -> Tuple[str]: # TODO
        if "=" in argument: return None
        return argument


class RtfmKey(Converter):
    """convert into a valid key"""
    
    async def convert(cls, ctx: ShakeContext, argument: Optional[str] = None) -> List[str]:
        return argument if not argument is None and argument in RTFM_PAGE_TYPES else None

class ValidKwarg(Converter):
    """Tries to convert into a valid cog"""
    
    async def convert(cls, ctx: ShakeContext, argument: str) -> Tuple[Any]: # TODO
        args = ()
        kwargs = dict()
        for ix, arg in enumerate(argument.split()):
            try: key, value = arg.split('=')
            except (TypeError, ValueError): 
                args = args + (arg,)
            else:
                kwargs[key] = literal_eval(value)
        return args, kwargs


class CleanChannels(Converter):
    _channel_converter = TextChannelConverter()

    async def convert(self, ctx: Context, argument: str) -> Union[Literal["*"], list[TextChannel]]:
        if argument == "*": 
            return "*"
        return [await self._channel_converter.convert(ctx, channel) for channel in argument.split()]


class DurationDelta(Converter):
    """dateutil.relativedelta.relativedelta"""

    async def convert(self, ctx: Context, duration: str) -> relativedelta:

        if not (delta := Duration(duration)):
            raise errors.BadArgument(_('`{duration}` is not a valid duration string.')).format(duration=duration)

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
            raise errors.BadArgument(f'`{duration}` results in a datetime outside the supported range.')


class Regex(Converter):
    async def convert(self, ctx: Context, argument: str) -> Pattern:
        match = fullmatch(r"`(.+?)`", argument)
        if not match:
            raise errors.BadArgument(_('Regex pattern missing wrapping backticks'))
        try:
            return compile(match.group(1), IGNORECASE + DOTALL)
        except error as e:
            raise errors.BadArgument(_('Regex error: {e_msg}')).format(e_msg=e.msg)


class Slash():
    bot: commands.Bot
    tree: CommandTree

    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot
        self.tree = self.bot.tree
        self.app_command: AppCommand = None
        self.command: Command = None

    async def __await__(self, command: Union[Command, str]) -> Slash:
        command = self.bot.get_command(command) if isinstance(command, str) else command
        if command == None:
            raise ValueError('Given Command is not found.')
        self.command = command
        self.app_command = await self.get_command()
        return self

    @property
    def is_group(self) -> bool:
        return any(
            isinstance(option, AppCommandGroup) 
                for option in self.app_command.options
        )

    @property
    def is_subcommand(self) -> bool:
        return any(
            isinstance(option == AppCommandGroup) and self.command.name in option.name
                for option in self.app_command.options
        )

    async def get_sub_command(self, sub_command: Command) -> tuple[AppCommand, str]:
        """Gets the app_command with its sub command(s) + its mention"""
        app_command = await self.get_command(sub_command.parent)
        
        if not self.is_group or not self.is_subcommand:
            return None
        
        custom_mention = f"</{app_command.name} {sub_command.name}:{app_command.id}>"
        return app_command, custom_mention


    async def get_command(self, command: Optional[AppCommand] = None) -> AppCommand:
        """Gets the AppCommand from a command (or command name)"""
        if (command := command or self.command) is None:
            raise ValueError('Argument `command` is not given/set')
        
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
    # extension: str = (ext[:-9] if ext.endswith('.__init__') else ext).split('.')[-1] # Exts.Commands.Other.reload.__init__ -> reload
    async def convert(self, ctx: ShakeContext, argument: str) -> str:

        def validation(final: str):
            if any(_ in str(final) for _ in ['load', 'unload', 'reload']):
                raise BadArgument(message=str(final) + ' is not a valid module to work with')
            return final

        if command := ctx.bot.get_command(argument):
            file = inspect.getfile(command.cog.__class__).removesuffix('.py')
            path = file.split('/')
            Exts = path.index('Exts')
            build = path[Exts:]
            return validation('.'.join(build))

        elif argument in ctx.bot.config.client.extensions:
            return validation(argument)
        
        

        elif len(parts := split(r'[./]', argument)) > 1:
            build = list(filter(lambda x: not x in ['__init__', 'py'], parts))

            try:
                Exts = build.index('Exts')
            except ValueError:
                fallback = '.'.join(build)
                if matches := ([_ for _ in ctx.bot.config.client.extensions if fallback in _] or get_close_matches(fallback, ctx.bot.config.client.extensions)):
                    return validation(matches[0])
                raise BadArgument(message='Specified module has an incorrect structure')

            extension = '.'.join(build[Exts:]) + '.__init__'

            if extension in ctx.bot.config.client.extensions:
                return validation(extension)
            
            elif matches := ([_ for _ in ctx.bot.config.client.extensions if extension in _] or get_close_matches(extension, ctx.bot.config.client.extensions)):
                return validation(matches[0])
            
        else:
            shortened = [_.split('.')[-1].lower() for _ in ctx.bot.config.client.extensions]
            if argument.lower() in shortened:
                return validation(ctx.bot.config.client.extensions[shortened.index(argument)])
            elif matches := get_close_matches(argument.lower(), shortened):
                return validation(ctx.bot.config.client.extensions[shortened.index(matches[0])])
        
        raise BadArgument(message='Specify either the module name or the path to the module')
#
############