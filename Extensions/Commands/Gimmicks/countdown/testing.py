############
#
from asyncio import sleep

from Classes import ShakeCommand, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        countdown = [_("five"), "four", "three", _("two"), _("one")]
        msg = await self.ctx.chat(_("{__} Lets start this {__}"))
        for num in countdown:
            await msg.edit(content="**:{0}:**".format(num))
            await sleep(1)
        await msg.edit(content="**:ok:** DING DING DING")


#
############
