############
#
from importlib import reload
from typing import Optional

from discord import Interaction, Message, PartialEmoji
from discord.abc import GuildChannel
from discord.app_commands import ContextMenu
from discord.ext.commands import ChannelNotFound, guild_only, hybrid_command, is_owner

from Classes import (
    GuildChannelConverter,
    ShakeBot,
    ShakeContext,
    Testing,
    _,
    extras,
    locale_doc,
    setlocale,
)

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
        self.menu = ContextMenu(
            name="shake channelinfo",
            callback=self.context_menu,
        )
        self.bot.tree.add_command(self.menu)

    def load(self) -> None:
        try:
            reload(channelinfo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="ℹ️")

    @guild_only()
    @setlocale()
    @is_owner()
    @locale_doc
    async def context_menu(self, interaction: Interaction, message: Message) -> None:
        ctx: ShakeContext = await ShakeContext.from_interaction(interaction)
        channel_id: GuildChannel = message.channel.id or interaction.channel_id
        await self.ci(ctx, str(channel_id))

    @hybrid_command(name="channelinfo", aliases=["ci"])
    @guild_only()
    @is_owner()
    @setlocale()
    @extras(beta=True)
    @locale_doc
    async def channelinfo(self, ctx: ShakeContext, *, channel: Optional[str] = None):
        _(
            """Get information about a specific channel.
            
            This command will show you some information about a channel.

            Parameters
            -----------
            channel: Optional[str]
                the channel mention, name or id to get information about"""
        )
        await self.ci(ctx, channel)

    async def ci(self, ctx: ShakeContext, channel: Optional[str] = None):
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
