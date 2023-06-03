############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..information import Information
from . import channelinfo, testing


########
#
class channelinfo_extension(Information):
    def __init__(self, bot: ShakeBot):
        super().__init__(bot=bot)
        try:
            reload(channelinfo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR LATIN SMALL LETTERS}")

    @hybrid_command(
        name="channelinfo",
        aliases=["ci"],
    )
    @guild_only()
    @setlocale()
    @locale_doc
    async def channelinfo(self, ctx: ShakeContext, *, characters: str) -> None:
        _(
            """Get information about a specific channel.
            
            This command will show you some information about a channel.

            Parameters
            -----------
            guild: Optional[str]
                the guild name or id to get information about"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else channelinfo

        try:
            await do.command(ctx=ctx, characters=characters).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(channelinfo_extension(bot))


#
############
