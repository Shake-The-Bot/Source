############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import command, guild_only, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..developing import Developing
from . import restart, testing


########
#
class restart_extension(Developing):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(restart)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(
            name="\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}"
        )

    @command(name="restart")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def restart(self, ctx: ShakeContext):
        _("""Stops and starts the bot like in a regular Restart""")
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else restart

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(restart_extension(bot))


#
############
