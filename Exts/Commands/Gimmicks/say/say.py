############
#
from Classes import ShakeContext, ShakeBot
########
#
class command():
    def __init__(self, ctx: ShakeContext, text: str, reply: bool):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.text: str = text
        self.reply: bool = reply

    async def __await__(self):
        if self.reply: 
            return await self.ctx.reply(self.text)
        return await self.ctx.smart_reply(self.text)
#
############