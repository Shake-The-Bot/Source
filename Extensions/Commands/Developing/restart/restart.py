############
#
import os
import sys

import launcher
from Classes import ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.to_success(
            ctx=self.ctx, description=_("Bot will restart now")
        )
        await self.ctx.chat(embed=embed)
        os.execl(sys.executable, os.path.abspath(launcher.__file__), *sys.argv)


#
############
