############
#
from importlib import reload
from typing import Optional

from discord import Member, PartialEmoji
from discord.ext.commands import (
    Greedy,
    bot_has_permissions,
    guild_only,
    has_permissions,
    hybrid_command,
)

from Classes import (
    DurationDelta,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    extras,
    locale_doc,
    setlocale,
)

from ..moderation import Moderation
from . import testing, timeout


########
#
class timeout_extension(Moderation):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(timeout)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="🚨")

    def category(self) -> str:
        return "moderation"

    @hybrid_command(name="timeout", aliases=["mute"])
    @guild_only()
    @extras(permissions=True)
    @has_permissions(moderate_members=True)
    @bot_has_permissions(moderate_members=True)
    @setlocale(guild=True)
    @locale_doc
    async def timeout(
        self,
        ctx: ShakeContext,
        member: Greedy[Member],
        time: DurationDelta = "1h",
        reason: Optional[str] = None,
    ):
        _(
            """Puts member(s) in the timeout of a given time (default 1h)

            Parameters
            -----------
            member: Greedy[discord.Member]
                the member(s) to timeout

            time: DurationDelta
                the time you want to timeout the member(s)
                
            reason: Optional[str]
                the reason why you put the member(s) in the timeout
                """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                ctx.testing = False
        do = testing if ctx.testing else timeout

        try:
            await do.command(
                ctx=ctx, member=member, time=time, reason=reason
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot):
    await bot.add_cog(timeout_extension(bot))


#
############
