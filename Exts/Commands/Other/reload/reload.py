############
#
from Classes import ShakeContext
from Classes.useful import cogs_handler
from Classes import ShakeBot
from Classes.converter import ValidCog
########
#
class command():
    def __init__(self, ctx: ShakeContext, extension: ValidCog):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.extension: str = extension

    async def __await__(self): 
        await cogs_handler(ctx=self.ctx, extensions=self.extension, method="reload")
        return
#
############