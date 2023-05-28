############
#
from random import randint
from typing import List
from discord import Member, Member
from Classes import _
from Classes import ShakeContext, ShakeBot, ShakeEmbed
########
#
class command():
    def __init__(self, ctx: ShakeContext, member: List[Member]):
        self.member: List[Member] = member
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self): 
        embed = ShakeEmbed.default(self.ctx, )
        embed.set_author(name=_("Peepee lenght"), icon_url="https://discord.com/assets/f1426431eb7c60fb8c072f90acb07ceb.svg")

        def genitiv_author(u: Member):
            return f"`{u.display_name}`\'s" if not u.display_name.endswith("s") else f"`{u.display_name}`'"

        for member in self.member: 
            pp = '='*randint(1, 15) if not await self.bot.is_owner(member) else '='*19
            embed.add_field(name=f"> {genitiv_author(member)} pp ({len(pp)+2}cm)", value=f"**8{pp}D**")
        return await self.ctx.smart_reply(embed=embed)
#
############