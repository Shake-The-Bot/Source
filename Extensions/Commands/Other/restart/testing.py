############
#
import os
import sys
from datetime import datetime, timedelta

from discord.utils import format_dt

import launcher
from Classes import ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        finished = format_dt(datetime.now() + timedelta(seconds=18), "R")
        embed = ShakeEmbed.to_success(
            ctx=self.ctx,
            description=_("bot will be restarted (about) {time}").format(time=finished),
        )
        await self.ctx.chat(embed=embed)
        os.execl(sys.executable, os.path.abspath(launcher.__file__), *sys.argv)


#
############
