############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji, TextChannel
from discord.ext.commands import ChannelNotFound, guild_only, hybrid_command
from discord.ext.commands.converter import GuildChannelConverter

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..information import Information
from . import channelinfo, testing


########
#
class channel_extension(Information):
    """
    server_cog
    """

    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        self.load()

    def load(self) -> None:
        try:
            reload(channelinfo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="ℹ️")

    @hybrid_command(name="channelinfo", aliases=["ci"])
    @guild_only()
    @setlocale()
    @extras(beta=True)
    @locale_doc
    async def channelinfo(self, ctx: ShakeContext, channel: Optional[str] = None):
        _(
            """Get information about a specific channel.
            
            This command will show you some information about a channel.

            Parameters
            -----------
            channel: Optional[str]
                the channel mention, name or id to get information about"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else channelinfo

        try:
            channel = await GuildChannelConverter().convert(
                ctx, str(channel or ctx.channel.id)
            )
        except ChannelNotFound:
            raise ChannelNotFound(
                _("Either this channel does not exist or I cant see it.")
            )

        try:
            await do.command(ctx=ctx, channel=channel).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(channel_extension(bot))


#
############
