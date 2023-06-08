############
#
from os import listdir
from random import choice

from discord import File, Member
from discord.ext import commands

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _
from Classes.useful import human_join


########
#
class command:
    def __init__(self, ctx: ShakeContext, member: commands.Greedy[Member] = None):
        self.member: commands.Greedy[Member] = member
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        description = _(
            "{members} stop spamming @everyone! \nIt's not that important..."
        ).format(
            members=human_join(
                seq=[member.mention for member in self.member],
                joke=self.member == [self.ctx.author],
            )
        )
        embed = ShakeEmbed.default(self.ctx, description=description)
        embed.set_author(name=f"@everyone?!")
        file_name = choice(listdir("./Assets/everyone"))
        file = File(
            f"./Assets/everyone/{file_name}", filename=f"image.{file_name[-3:]}"
        )
        embed.set_image(url=f"attachment://image.{file_name[-3:]}")
        await self.ctx.chat(embed=embed, files=[file])
        return


#
############
