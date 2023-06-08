from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar, Union

from discord import utils
from discord.ext.commands import Command, Context, check
from discord.ext.commands._types import BotT, Check
from typing_extensions import ParamSpec

from Classes.exceptions import NotVoted
from Classes.useful import votecheck

__all__ = ("event_check", "has_voted", "extras")

T = TypeVar("T")
P = ParamSpec("P")
Coro = Coroutine[Any, Any, T]
MaybeCoro = Union[T, Coro]

_Event = Callable[..., Coro[None]]
_WrappedEvent = Callable[[_Event], _Event]


def event_check(event_predicate: Callable[P, MaybeCoro[bool]]) -> _WrappedEvent:
    def wrapper(event: _Event) -> _Event:
        setattr(event, "callback", event)

        @wraps(event)
        async def inner(*args: P.args, **kwargs: P.kwargs) -> None:
            if await utils.maybe_coroutine(event_predicate, *args, **kwargs):
                await event(*args, **kwargs)

        return inner

    setattr(wrapper, "predicate", event_predicate)
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
            raise NotVoted("You did not vote for me in the last 12h.")
        return True

    return check(predicate)


def extras(
    func: Optional[T] = None, **kwargs: Dict[Any, bool]
) -> Callable[[Optional[T], bool], T]:
    """A decorator that indicates this command is in/needs something.

    This is **not** implemented as a :func:`check`, and is instead verified by Shake side.
    Currently, there is no extra error handler called when a command raises any errors.

    Examples
    ---------

    .. code-block:: python3

        @commands.hybrid_command()
        @extras(owner=True)
        async def my_beta_command(ctx: ShakeContext) -> None:
            await ctx.send('I am a beta command!')
    """

    def inner(f: T) -> T:
        if isinstance(f, Command):
            f.extras.update(kwargs)
        else:
            try:
                f.extras.update(kwargs)  # type: ignore # Runtime attribute access
            except AttributeError:
                f.extras = kwargs  # type: ignore # Runtime attribute assignment
        return f

    if func is None:
        return inner
    else:
        return inner(func)
