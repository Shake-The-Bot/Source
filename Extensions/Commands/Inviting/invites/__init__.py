############
#
from importlib import reload
from typing import Optional

from discord import Member, PartialEmoji
from discord.ext.commands import Cog, guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from . import invites, testing


########
#
class invites_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot
        try:
            reload(invites)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{DESKTOP COMPUTER}")

    @hybrid_command(name="invites")
    @guild_only()
    @setlocale()
    @locale_doc
    async def invites(
        self, ctx: ShakeContext, *, member: Optional[Member] = None
    ) -> None:
        _(
            """See the users amount of invites.

            Parameters
            -----------
            member: discord.Member
                the member
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else invites

        try:
            await do.command(ctx=ctx, member=member or ctx.author).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(invites_extension(bot))


#
############
