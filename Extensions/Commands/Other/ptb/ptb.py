#############
#
from discord import Guild
from discord.ext.commands.converter import (
    GuildConverter,
    TextChannelConverter,
    UserConverter,
)
from discord.ext.commands.errors import (
    BadArgument,
    ChannelNotFound,
    GuildNotFound,
    UserNotFound,
)

from Classes import MISSING, ShakeCommand, ShakeEmbed, _

########
# "


class command(ShakeCommand):
    def __init__(self, ctx, id: int):
        super().__init__(ctx)
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
                raise BadArgument("Given ID is not from a discord object.")

        except BadArgument:
            embed = ShakeEmbed.to_error(
                self.ctx,
                description=_(
                    "Your input does not match any server/channel/user I can find"
                ),
            )
            return await self.ctx.chat(embed=embed)

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
