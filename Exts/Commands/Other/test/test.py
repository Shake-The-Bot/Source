#############
#
from Classes import ShakeBot, ShakeContext, MISSING, ShakeEmbed, _
from discord.ext.commands.errors import GuildNotFound, UserNotFound, ChannelNotFound
from discord.ext.commands.converter import TextChannelConverter, GuildConverter, UserConverter
########
#
class EveryNone(Exception):
    """Example of Exception"""

class command():
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
            else:
                name = _("user")

            try:
                channel = await TextChannelConverter().convert(self.ctx, self.id)
            except ChannelNotFound:
                channel = MISSING
            else:
                name = _("channel")

            try:
                guild = await GuildConverter().convert(self.ctx, self.id)
            except GuildNotFound:
                guild = MISSING
            else:
                name = _("guild")
        
            if all([not guild, not user, not channel]):
                raise EveryNone
            
        except EveryNone:
            embed = ShakeEmbed.to_error(self.ctx, description=_("Your input does not match any server/channel/user I can find"))
            await self.ctx.smart_reply(embed=embed)
            return
        
        else:
            if (guild or channel or user).id in list(self.bot.tests.keys()):
                del self.bot.tests[(guild or channel or user).id]
                description=_("The specified {name} is __removed__ to the public test build").format(name=name)
            else:
                self.bot.tests[(guild or channel or user).id] = guild or channel or user
                description = _("The specified {name} is temporarily __added__ to the public test build").format(name=name)
            
            embed = ShakeEmbed.to_success(self.ctx, description=description)
            await self.ctx.smart_reply(embed=embed)
            return
        
#
############