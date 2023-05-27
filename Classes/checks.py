from __future__ import annotations
from discord import utils
from discord.ext.commands import Command, Group, check, Context, hybrid_command
from functools import wraps
from typing_extensions import ParamSpec
from .useful import votecheck
from .exceptions import NotVoted
from discord.ext.commands._types import Check, BotT

from typing import (
    Any, Callable, Coroutine, TypeVar, Union,
    Optional
)

__all__ = ('event_check', 'is_beta', 'has_voted', 'extras')

T = TypeVar("T")
P = ParamSpec('P')
Coro = Coroutine[Any, Any, T]
MaybeCoro = Union[T, Coro]

_Event = Callable[..., Coro[None]]
_WrappedEvent = Callable[[_Event], _Event]


def event_check(event_predicate: Callable[P, MaybeCoro[bool]]) -> _WrappedEvent:
    def wrapper(event: _Event) -> _Event:
        setattr(event, 'callback', event)

        @wraps(event)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            if await utils.maybe_coroutine(event_predicate, *args, **kwargs):
                await event(*args, **kwargs)
        return inner

    setattr(wrapper, 'predicate', event_predicate)
    return wrapper


def has_voted() -> Check[Any]:
    """A :func:`.check` that checks if the person has voted for the bot.

    This is powered by :meth:`.Bot.is_vote`.

    This check raises a special exception, :exc:`.NotVoted` that is derived
    from :exc:`.CheckFailure`.

    Examples
    ---------

    .. code-block:: python3

        @commands.hybrid_command()
        @has_voted()
        async def my_beta_command(ctx: ShakeContext) -> None:
            await ctx.send('You have voted for me in the last 12h, Thank you!!')
    """
    async def predicate(ctx: Context[BotT]) -> bool:
        if not await votecheck(ctx):
            raise NotVoted('You did not vote for me in the last 12h.')
        return True
    return check(predicate)


def is_beta(func: Optional[T] = None) -> Union[T, Callable[[T], T]]:
    """A decorator that indicates this command is in beta.

    This is **not** implemented as a :func:`check`, and is instead verified by Shake side.
    Currently, there is no extra error handler called when a beta command raises any errors.

    Examples
    ---------

    .. code-block:: python3

        @commands.hybrid_command()
        @is_beta()
        async def my_beta_command(ctx: ShakeContext) -> None:
            await ctx.send('I am a beta command!')
    """
    def inner(f: T) -> T:
        if isinstance(f, (Command, Group)):
            f.extras['beta'] = True
        else:
            pass
        return f

    if func is None:
        return inner
    else:
        return inner(func)
    

def extras(**kwargs: bool) -> Callable[[T], T]:
    def decorator(inner: T) -> T:
        if isinstance(inner, Command): 
            inner.extras.update(kwargs)
        else:
            try:
                inner.extras.update(kwargs)  # type: ignore # Runtime attribute access
            except AttributeError:
                inner.extras = kwargs  # type: ignore # Runtime attribute assignment

        return inner
    return decorator