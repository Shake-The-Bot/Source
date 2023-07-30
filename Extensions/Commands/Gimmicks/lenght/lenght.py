############
#
from random import randint
from typing import List

from discord import Member

from Classes import Format, ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    def __init__(self, ctx, member: List[Member]):
        super().__init__(ctx)
        self.member: List[Member] = member

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
            title=_("Length"),
        )

        for member in self.member:
            if await self.bot.is_owner(member):
                lenght = "=" * 21
            else:
                lenght = "=" * randint(1, 17)

            embed.add_field(
                name=Format.blockquotes(Format.join(member, f"({len(lenght)}cm)")),
                value=Format.multicodeblock(f"{lenght}", "python"),
            )
        return await self.ctx.chat(embed=embed)


#
############
