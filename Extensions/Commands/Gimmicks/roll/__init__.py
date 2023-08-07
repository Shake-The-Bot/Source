############
#
from importlib import reload
from typing import Optional

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from ..gimmicks import Gimmicks
from . import roll, testing


########
#
class roll_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(roll)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{GAME DIE}")

    @hybrid_command(name="roll")
    @guild_only()
    @locale_doc
    @setlocale()
    async def roll(
        self, ctx: ShakeContext, start: Optional[int] = 1, end: Optional[int] = 6
    ):
        _(
            """Displays a random number in a specified range of values. (Default: 1-6)

            Parameters
            -----------
            start: Optional[int]
                the start to roll at

            end: Optional[int]
                the endlimit to roll till"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else roll
        try:
            await do.command(ctx=ctx, start=start, end=end).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(roll_extension(bot))


#
############
