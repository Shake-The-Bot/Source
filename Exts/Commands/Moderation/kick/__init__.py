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

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..moderation import Moderation
from . import kick, testing


########
#
class kick_extension(Moderation):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(kick)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="🚨")

    @hybrid_command(name="kick")
    @guild_only()
    @extras(permissions=True)
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    @setlocale(guild=True)
    @locale_doc
    async def kick(
        self, ctx: ShakeContext, member: Greedy[Member], *, reason: Optional[str] = None
    ):
        _(
            """kicks a member

            Parameters
            -----------
            member: Greedy[discord.Member]
                the member(s) to kick
                
            reason: Optional[str]
                the reason why you kicked the member(s)
                """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else kick

        try:
            await do.command(ctx=ctx, member=member, reason=reason).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(kick_extension(bot))


#
############
