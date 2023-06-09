############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji, TextChannel
from discord.ext.commands import guild_only, hybrid_group

from Classes import ShakeBot, ShakeContext, Slash, Testing, _, locale_doc, setlocale

from ..games import Games
from . import aboveme, testing


########
#
class aboveme_extension(Games):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(aboveme)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{SQUARED UP WITH EXCLAMATION MARK}")

    @hybrid_group(name="aboveme")
    @guild_only()
    @setlocale()
    @locale_doc
    async def aboveme(self, ctx: ShakeContext):
        _(
            """Throw nice, funny and sometimes annoying comments to the user above you! 
            The AboveMe game offers a lot of fun and creats entertaining moments among each other!"""
        )
        ...

    @aboveme.command(name="setup")
    @guild_only()
    @setlocale()
    @locale_doc
    async def setup(
        self,
        ctx: ShakeContext,
        /,
        channel: Optional[TextChannel] = None,
        hardcore: Optional[bool] = False,
    ):
        _(
            """Setup the whole AboveMe game in seconds
            Get more information about the aboveme game with /aboveme info"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else aboveme

        try:
            await do.command(ctx=ctx, channel=channel, hardcore=hardcore).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(aboveme_extension(bot))


#
############
