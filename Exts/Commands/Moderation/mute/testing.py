############
#
from datetime import timedelta
from Classes.i18n import _
from Classes import ShakeContext, ShakeEmbed
########
#
class command():
    def __init__(self, ctx: ShakeContext, member, time):
        self.bot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.member = member
        self.time = time
    
    async def __await__(self):
        convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        time = int(self.time[0]) * convert[self.time[-1]]
        try:
            for member in self.member: 
                await member.timeout(timedelta(seconds=time), reason="mute command executed by {}".format(self.ctx.author))
        except Exception as error:
            raise error
        else:
            embed = ShakeEmbed.default(self.ctx, description = _("{emoji} {prefix} The specified members were successfully muted").format(
                emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix
            ))
            await self.ctx.smart_reply(embed=embed)
        finally:
            return
#
############