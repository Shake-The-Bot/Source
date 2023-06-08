############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..information import Information
from . import plus, testing


########
#
class plus_extension(Information):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(plus)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{GEM STONE}")

    @hybrid_command(
        name="premium",
        aliases=[
            "shake+",
        ],
    )
    @extras(beta=True, owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def premium(self, ctx: ShakeContext):
        _(
            """Get information about Shake+.

            Of course, you dont need it tho. It's like a tip"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else plus

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(plus_extension(bot))


#
############
