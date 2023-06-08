############
#
from importlib import reload
from typing import Optional

from discord import Member, PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import rainbow, testing


########
#
class rainbow_extension(Gimmicks):
    def __init__(self, bot: ShakeBot):
        super().__init__(bot=bot)
        try:
            reload(rainbow)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{RAINBOW}")

    @hybrid_command(name="rainbow")
    @guild_only()
    @setlocale()
    @locale_doc
    async def rainbow(self, ctx: ShakeContext, member: Optional[Member] = None):
        _(
            """Show your support to LGBT+ with a rainbow filter! ^^

            Parameters
            -----------
            member: discord.Member
                the member to add"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rainbow

        try:
            await do.command(
                ctx=ctx,
                member=member or ctx.author,
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(rainbow_extension(bot))


#
############
