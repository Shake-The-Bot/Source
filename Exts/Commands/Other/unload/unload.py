############
#
from Classes import ShakeContext
from Classes.useful import cogs_handler
from Classes.converter import ValidCog
from Classes import ShakeBot
########
#
class command():
    def __init__(self, ctx: ShakeContext, extension: ValidCog):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.extension: str = extension

    async def __await__(self): 
        await cogs_handler(ctx=self.ctx, extensions=self.extension, method='unload')
        return
#
############