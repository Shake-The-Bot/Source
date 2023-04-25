############
#
from __future__ import annotations
from ast import literal_eval
from difflib import get_close_matches
from typing import Union, Literal, Any, Tuple, TYPE_CHECKING, Optional, List
from re import error, fullmatch, DOTALL, IGNORECASE, Pattern, compile, split
from dateutil.relativedelta import relativedelta
from discord import TextChannel
import inspect
from discord.ext.commands import Context, Converter, TextChannelConverter, errors, BadArgument
from datetime import datetime, timezone

if TYPE_CHECKING:
    from Classes import _, MISSING
    from .helpful import ShakeContext
    from .useful import Duration, RTFM_PAGE_TYPES


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
        kwargs = {}
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



class ValidCog(Converter): # beta, working on it rn
    """Tries to find a matching extension and returns it

    Triggers a BadArgument error if you specify the extensions "load", "unload" or "reload", 
    because they are excluded before this function
    """
    # extension: str = (get some pingext[:-9] if ext.endswith('.__init__') else ext).split('.')[-1] # Exts.Commands.Other.reload.__init__ -> reload
    async def convert(self, ctx: ShakeContext, argument: str) -> str:

        def final(ext: str):
            if any(x in str(ext) for x in ('load', 'unload', 'reload')):
                raise BadArgument(message=str(ext) + ' is not a valid module to work with')
            return ext

        if command := ctx.bot.get_command(argument):
            file = inspect.getfile(command.cog.__class__).removesuffix('.py')
            path = file.split('/')
            index = path.index('Exts')
            correct = path[index:]
            return final('.'.join(correct))

        if argument in ctx.bot.config.client.extensions:
            return final(argument)
        
        if len(parts := split('.|/', argument)) > 1:
            ext = '.'.join(filter(lambda x: not any(x == y for y in ('py', '__init__')), parts)) + '.__init__'
            if ext in ctx.bot.config.client.extensions:
                return final(ext)
            
        if matches := (
            [ext for ext in ctx.bot.config.client.extensions if ext in ctx.bot.config.client.extensions] or 
            get_close_matches(argument, ctx.bot.config.client.extensions)
        ):
            return final(matches[0])
        else:
            shortened_exts = [ext.split('.')[-1].lower() for ext in ctx.bot.config.client.extensions]

            if argument in shortened_exts:
                return final(ctx.bot.config.client.extensions[shortened_exts.index(argument)])
            elif matches := get_close_matches(argument, shortened_exts):
                return final(ctx.bot.config.client.extensions[shortened_exts.index(matches[0])])
            else:
                raise BadArgument(message='Specify either the module name or the path to the module')
        

# class ValidCog(Converter):
#     """Tries to convert into a valid cog"""
#     @classmethod
#     async def convert(cls, ctx: ShakeContext, argument: str) -> List[str]: # TODO: discord.utils._unique, invite_tracking 
#         if (command := ctx.bot.get_command(argument)) and getattr(ctx.bot.get_command(argument).cog, 'category', None):
#             if path.isfile(f'./exts/commands/{command.cog.category()}/{command.qualified_name}/__init__.py'): 
#                 return [f'exts.commands.{command.cog.category()}.{command.qualified_name}.__init__']
#         extensions = {
            
#                 'exts.{}.{}.{}.__init__'.format(precategory, category, folder) if path.isfile('./exts/{}/{}/{}/__init__.py'.format(precategory, category, folder)) 
#                 else 'exts.{}.{}.{}.{}.__init__'.format(precategory, category, folder, subfolder) if path.isfile('./exts/{}/{}/{}/{}/__init__.py'.format(precategory, category, folder, subfile))
#                 else None
            
#             for precategory in listdir(f'./exts') if path.isdir(f'./exts/{precategory}')
#             for category in listdir(f'./exts/{precategory}') if path.isdir(f'./exts/{precategory}/{category}')
#             for folder in listdir(f'./exts/{precategory}/{category}') if path.isdir(f'./exts/{precategory}/{category}/{folder}')
#             for subfolder in listdir(f'./exts/{precategory}/{category}/{folder}') if path.isdir(f'./exts/{precategory}/{category}/{folder}/{subfolder}')
#             for subfile in listdir(f'./exts/{precategory}/{category}/{folder}/{subfolder}')
#             for file in listdir(f'./exts/{precategory}/{category}/{folder}') if file[-11:] == "__init__.py"
            
#         }
#         rturn = ['bot'] if argument in ('bot', 'client', 'self') else (list(extensions) if (not argument or argument in ('all', '*', 'everything', 'every')) else [argument.replace('.__init__', '')+'.__init__' if argument.replace('.__init__', '') in [x.replace('.__init__', '') for x in extensions] else None])
#         if bool(rturn) and not None in rturn: return rturn
#         raise BadArgument()
#
############