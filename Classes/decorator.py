from __future__ import annotations

from ast import AsyncFunctionDef, Call, ClassDef, Expr, Name, Str, parse
from functools import wraps
from inspect import cleandoc, getsource
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    TypeVar,
    Union,
)

from discord import Interaction, Permissions, utils
from discord.ext.commands import Command, Context, MissingPermissions, check
from discord.ext.commands._types import BotT, Check
from typing_extensions import ParamSpec

from Classes.exceptions import NotVoted
from Classes.i18n import current
from Classes.useful import votecheck

if TYPE_CHECKING:
    from Classes.helpful import ShakeBot, ShakeContext

__all__ = ("event_check", "has_voted", "extras", "has_permissions")

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


def has_permissions(testing: Optional[bool] = False, **perms: bool) -> Check[Any]:
    """A :func:`.check` that is added that checks if the member has all of
    the permissions necessary.

    Note that this check operates on the current channel permissions, not the
    guild wide permissions.

    The permissions passed in must be exactly like the properties shown under
    :class:`.discord.Permissions`.

    This check raises a special exception, :exc:`.MissingPermissions`
    that is inherited from :exc:`.CheckFailure`.

    Parameters
    ------------
    perms
        An argument list of permissions to check for.

    Example
    ---------

    .. code-block:: python3

        @bot.command()
        @commands.has_permissions(manage_messages=True)
        async def test(ctx):
            await ctx.send('You can manage messages.')

    """

    invalid = set(perms) - set(Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(ctx: ShakeContext) -> bool:
        permissions = ctx.permissions

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True
        if testing and ctx.testing:
            return True

        raise MissingPermissions(missing)

    return check(predicate)


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
        @extras(beta=True)
        async def my_beta_command(ctx: ShakeContext) -> None:
            await ctx.send('I am a beta command!')
    """

    def inner(f: T) -> T:
        if isinstance(f, Command):
            f.extras.update(kwargs)
        else:
            try:
                f.extras.update(kwargs)
            except AttributeError:
                f.extras = kwargs
        return f

    if func is None:
        return inner
    else:
        return inner(func)


def setlocale(guild: Optional[bool] = False) -> Check[Any]:
    async def predicate(
        ctx: Optional[Context] = None, interaction: Optional[Interaction] = None
    ) -> bool:
        if isinstance(interaction, Interaction):
            if interaction.command:
                ctx = await Context.from_interaction(ctx)
            else:
                return False
        bot: ShakeBot = ctx.bot

        if guild:
            locale = await bot.i18n.get_guild(ctx.guild.id, default="en-US")
        else:
            locale = await bot.i18n.get_user(ctx.author.id, default="en-US")
        current.set(locale)
        return True

    return check(predicate)


def i18n_docstring(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    src = getsource(func)
    try:
        parsed_tree = parse(src)
    except IndentationError:
        parsed_tree = parse("class Foo:\n" + src)
        assert isinstance(parsed_tree.body[0], ClassDef)
        function_body: ClassDef = parsed_tree.body[0]
        assert isinstance(function_body.body[0], AsyncFunctionDef)
        tree: AsyncFunctionDef = function_body.body[0]
    else:
        assert isinstance(parsed_tree.body[0], AsyncFunctionDef)
        tree = parsed_tree.body[0]

    if not isinstance(tree.body[0], Expr):
        return func

    gettext_call = tree.body[0].value
    if not isinstance(gettext_call, Call):
        return func

    if not isinstance(gettext_call.func, Name) or gettext_call.func.id != "_":
        return func

    assert len(gettext_call.args) == 1
    assert isinstance(gettext_call.args[0], Str)

    func.__doc__ = cleandoc(gettext_call.args[0].s)
    return func


locale_doc = i18n_docstring
