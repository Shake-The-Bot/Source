############
#
from discord import Member
from discord.ext.commands import Greedy
from Classes import ShakeContext, ShakeBot
#########
#
class rank_command():
    def __init__(self, ctx: ShakeContext, member: Greedy[Member]):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.member: Greedy[Member] = member
    
    async def __await__(self):
        pass
#
############