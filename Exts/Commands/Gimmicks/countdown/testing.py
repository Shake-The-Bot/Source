############
#
from Classes.i18n import _
from Classes import ShakeContext, ShakeBot
from asyncio import sleep
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        countdown = [_('five'), 'four', 'three', _('two'), _('one')]
        msg = await self.ctx.smart_reply('**'+_('Lets start this')+'**')
        for num in countdown:
            await msg.edit(content='**:{0}:**'.format(num))
            await sleep(1)
        await msg.edit(content='**:ok:** DING DING DING')
#
############