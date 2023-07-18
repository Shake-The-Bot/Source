############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import command, guild_only, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..developing import Developing
from . import bash, testing


########
#
class bash_extension(Developing):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(bash)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{DESKTOP COMPUTER}")

    @command(name="bash")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def bash(self, ctx: ShakeContext, *, command: str) -> None:
        _(
            """Run shell commands.

            Parameters
            -----------
            command: str
                the command"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else bash

        try:
            await do.command(ctx=ctx, command=command).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(bash_extension(bot))


#
############
