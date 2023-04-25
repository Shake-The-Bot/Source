############
#
from Classes import ShakeContext
from Classes.useful import cogshandler, Methods
from Classes import ShakeBot
from Classes.converter import ValidCog
########
#
class command():
    def __init__(self, ctx: ShakeContext, method: Methods, extension: ValidCog):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.method: Methods = method
        self.extension: str = extension

    async def __await__(self): 
        embed = await cogshandler(ctx=self.ctx, method=self.method, extensions=self.extension)
        return await self.ctx.smart_reply(embed=embed)
#
############