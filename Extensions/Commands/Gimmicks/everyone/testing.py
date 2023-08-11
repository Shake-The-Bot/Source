############
#
from os import listdir
from random import choice

from discord import File, Member
from discord.ext import commands

from Classes import ShakeCommand, ShakeEmbed, _
from Classes.useful import human_join


########
#
class command(ShakeCommand):
    def __init__(self, ctx, member: commands.Greedy[Member] = None):
        super().__init__(ctx)
        self.member: commands.Greedy[Member] = member

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
        file_url = choice(
            self.bot.assets.everyone.animated + self.bot.assets.everyone.static
        )
        embed.set_image(url=file_url)
        return await self.ctx.chat(embed=embed)


#
############
