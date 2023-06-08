############
#
from discord import Object

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(self, ctx: ShakeContext, guild: Object):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.guild: Object = guild

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        if not (
            guild := self.bot.get_guild(self.guild) if self.guild else self.ctx.guild
        ):
            embed.description = (
                "**" + _("{emoji} {prefix} The given server is not valid") + "**"
            ).format(emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix)
        else:
            try:
                await guild.leave()
            except:
                embed.description = (
                    "**"
                    + _("{emoji} {prefix} leaving the guild raised an error")
                    + "**"
                ).format(emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix)

            else:
                embed.description = (
                    "**" + _("{emoji} {prefix} I'll leave the given server") + "**"
                ).format(emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix)
        await self.ctx.chat(embed=embed)


#
############
