############
#
from asyncio import sleep

from Classes import ShakeBot, ShakeContext, _


########
#
class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        countdown = [_("five"), "four", "three", _("two"), _("one")]
        msg = await self.ctx.chat("**" + _("Lets start this") + "**")
        for num in countdown:
            await msg.edit(content="**:{0}:**".format(num))
            await sleep(1)
        await msg.edit(content="**:ok:** DING DING DING")


#
############
