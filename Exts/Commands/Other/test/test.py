#############
#
from Classes import ShakeBot
from Classes.useful import captcha
from Classes import ShakeContext
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        file, password = await captcha(self.bot)
        return await self.ctx.smart_reply(password, file=file)
#
############