############
#
from Classes import ShakeContext, ShakeBot, ShakeEmbed
from Classes.i18n import _
from discord import Object
########
#
class command():
    def __init__(self, ctx: ShakeContext, guild: Object):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.guild: Object = guild

    async def __await__(self): 
        embed = ShakeEmbed.default(self.ctx, )
        if not (guild := self.bot.get_guild(self.guild) if self.guild else self.ctx.guild):
            embed.description = ('**'+_('{emoji} {prefix} The given server is not valid')+'**').format(
                emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix)
        embed.description = ('**'+_('{emoji} {prefix} I\'ll leave the given server')+'**').format(
                emoji=self.bot.emojis.hook, prefix=self.bot.emojis.prefix)
        await self.ctx.smart_reply(embed=embed)
        try:
            await guild.leave()
        except:
            pass
        finally:
            return
#
############