############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..information import Information
from . import ping, testing


########
#
class ping_extension(Information):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(ping)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{CHART WITH UPWARDS TREND}")

    @hybrid_command(name="ping")
    @guild_only()
    @setlocale()
    @locale_doc
    async def ping(self, ctx: ShakeContext):
        _("""Get some ping""")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else list

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(ping_extension(bot))


#
############
