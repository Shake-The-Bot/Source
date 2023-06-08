############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import countdown, testing


########
#
class countdown_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(countdown)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR NUMBERS}")

    @hybrid_command(name="countdown")
    @guild_only()
    @setlocale()
    @locale_doc
    async def countdown(self, ctx: ShakeContext):
        _("""It's the final countdown""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else countdown

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(countdown_extension(bot))


#
############
