############
#
from importlib import reload
from typing import Optional

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from ..gimmicks import Gimmicks
from . import random, testing


########
#
class random_extension(Gimmicks):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(random)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @hybrid_command(name="random")
    @guild_only()
    @locale_doc
    @setlocale()
    async def random(self, ctx: ShakeContext, offline: Optional[bool] = True):
        _(
            """Picks a random online user

            Parameters
            -----------
            offline: bool
                if offline is ok"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else random

        try:
            await do.command(ctx=ctx, offline=offline).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


########
#
async def setup(bot: ShakeBot):
    await bot.add_cog(random_extension(bot))


#
############
