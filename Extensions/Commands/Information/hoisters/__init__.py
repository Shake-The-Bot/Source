############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, has_permissions, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..information import Information
from . import hoisters, testing


########
#
class hoisters_extension(Information):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(hoisters)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{SQUARED UP WITH EXCLAMATION MARK}")

    @hybrid_command(name="hoisters")
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def hoisters(self, ctx: ShakeContext):
        _("""Shows a sorted list of members that have a nicknname""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else hoisters

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(hoisters_extension(bot))


#
############
