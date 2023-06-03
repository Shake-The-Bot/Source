############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import Cog, guild_only, hybrid_command, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..information import Information
from . import testing, vote


########
#
class vote_extension(Information):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(vote)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{CROWN}")

    @hybrid_command(name="vote")
    @extras(beta=True, owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def vote(self, ctx: ShakeContext):
        _(
            """Get information about Shake+.

            Of course, you dont have to. It's like a tip"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else vote

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(vote_extension(bot))


#
############
