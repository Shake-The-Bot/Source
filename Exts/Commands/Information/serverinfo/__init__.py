############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji
from discord.ext.commands import Cog
from discord.ext.commands import GuildNotFound as _GuildNotFound
from discord.ext.commands import guild_only, hybrid_command
from discord.ext.commands.converter import GuildConverter

from Classes import (
    GuildNotFound,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    locale_doc,
    setlocale,
)

from ..information import Information
from . import serverinfo, testing


########
#
class server_extension(Information):
    """
    server_cog
    """

    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        self.load()

    def load(self) -> None:
        try:
            reload(serverinfo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="ℹ️")

    @hybrid_command(name="serverinfo", aliases=["si"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def serverinfo(self, ctx: ShakeContext, guild: Optional[str] = None):
        _(
            """Get information about a specific server.
            
            This command will show you some information about a server.

            Parameters
            -----------
            guild: Optional[str]
                the guild name or id to get information about"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                ctx.testing = False

        do = testing if ctx.testing else serverinfo

        try:
            guild = await GuildConverter().convert(self, str(guild or ctx.guild.id))
        except _GuildNotFound as argument:
            raise GuildNotFound(
                argument, _("Either this server does not exist or I am not on it.")
            )

        try:
            await do.command(ctx=ctx, guild=guild).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(server_extension(bot))


#
############
