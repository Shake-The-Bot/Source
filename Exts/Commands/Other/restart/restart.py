############
#
from Classes import ShakeContext, ShakeBot, ShakeEmbed, _
import os, sys, launcher
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self): 
        embed = ShakeEmbed.to_success(ctx=self.ctx, description=_("Bot will restart now"))
        await self.ctx.smart_reply(embed=embed)
        os.execl(sys.executable, os.path.abspath(launcher.__file__), *sys.argv) 
#
############