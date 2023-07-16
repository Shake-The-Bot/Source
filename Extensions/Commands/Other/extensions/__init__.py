############
#
from importlib import reload
from typing import Literal

from discord import PartialEmoji
from discord.ext.commands import Greedy, command, guild_only, is_owner

from Classes import (
    ShakeBot,
    ShakeContext,
    Testing,
    ValidExt,
    _,
    extras,
    locale_doc,
    setlocale,
)
from Classes.types import ExtensionMethods

from ..other import Other
from . import extensions, testing


########
#
class extensions_extension(Other):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(extensions)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(
            name="\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}"
        )

    @command(name="extensions", aliases=["exts", "cogs"])
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def extensions(
        self,
        ctx: ShakeContext,
        command: Literal["load", "unload", "reload"],
        *,
        extension: Greedy[ValidExt]
    ):
        _(
            """Reloads, unloads or loads extensions/commands of the bot
            
            Parameters
            -----------
            command: Literal[load, unload, reload]
                re- un- or loading the <extensions>

            extension: Greedy[ValidExt]
                the extension(s) you want to re- un- or load"""
        )
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else extensions

        try:
            await do.command(
                ctx=ctx, method=ExtensionMethods[command], extension=extension
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(extensions_extension(bot))


#
############
