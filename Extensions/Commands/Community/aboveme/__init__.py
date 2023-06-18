############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji, TextChannel
from discord.ext.commands import guild_only, has_permissions, hybrid_group

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..community import Community
from . import aboveme, testing


########
#
class aboveme_extension(Community):
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
    @has_permissions(administrator=True)
    @extras(permissions=True)
    @locale_doc
    async def setup(
        self,
        ctx: ShakeContext,
        /,
        channel: Optional[TextChannel] = None,
        react: Optional[bool] = None,
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
            await do.command(ctx=ctx).setup(channel=channel, react=react)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(aboveme_extension(bot))


#
############
