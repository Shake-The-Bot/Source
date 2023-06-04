############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji
from discord.ext.commands import command, guild_only, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..other import Other
from . import dispatch, testing


########
#
class dispatch_extension(Other):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(dispatch)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{PISTOL}")

    @command(name="dispatch")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def dispatch(self, ctx: ShakeContext, event: Optional[str], kwargs):
        _(
            """Send an event

            Parameters
            -----------
            event: Optional[str]
                the name of the event

            kwargs: Any
                event keyword arguments"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else dispatch

        try:
            await do.command(ctx, event, kwargs).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(dispatch_extension(bot))


#
############
