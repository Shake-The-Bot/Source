#############
#
from discord import Guild
from discord.ext.commands.converter import (
    GuildConverter,
    TextChannelConverter,
    UserConverter,
)
from discord.ext.commands.errors import ChannelNotFound, GuildNotFound, UserNotFound

from Classes import MISSING, ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class EveryNone(Exception):
    """Example of Exception"""


class command:
    def __init__(self, ctx: ShakeContext, id: int):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.id: int = id

    async def __await__(self):
        try:
            try:
                user = await UserConverter().convert(self.ctx, self.id)
            except UserNotFound:
                user = MISSING

            try:
                channel = await TextChannelConverter().convert(self.ctx, self.id)
            except ChannelNotFound:
                channel = MISSING

            try:
                guild = await GuildConverter().convert(self.ctx, self.id)
            except GuildNotFound:
                guild = MISSING

            if all([not guild, not user, not channel]):
                raise EveryNone

        except EveryNone:
            embed = ShakeEmbed.to_error(
                self.ctx,
                description=_(
                    "Your input does not match any server/channel/user I can find"
                ),
            )
            await self.ctx.chat(embed=embed)
            return

        else:
            current = guild or channel or user
            name = getattr(
                current,
                "mention",
                _("Server") if isinstance(current, Guild) else current.name,
            )
            if current.id in set(self.bot.testing.keys()):
                del self.bot.testing[current.id]
                description = _(
                    "{name} is __removed__ from the public test build"
                ).format(name=name)
            else:
                self.bot.testing[current.id] = guild or channel or user
                description = _(
                    "{name} is temporarily __added__ to the public test build"
                ).format(name=name)

            embed = ShakeEmbed.to_success(self.ctx, description=description)
            await self.ctx.chat(embed=embed)
            return


#
############
