############
#
from typing import Optional

from discord import Member
from discord.ext.commands import Greedy

from Classes import ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    def __init__(self, ctx, member: Greedy[Member], reason: Optional[str]):
        super().__init__(ctx)
        self.member: Greedy[Member] = member
        self.reason: Optional[str] = reason or _("No reason provided")

    async def __await__(self):
        try:
            for member in self.member:
                await member.kick(
                    reason="{reason} ({author})".format(
                        author=self.ctx.author, reason=self.reason
                    )
                )
        except Exception as error:
            raise error
        else:
            embed = ShakeEmbed.to_success(
                self.ctx,
                description=_("The specified member(s) got successfully kicked"),
            )
            await self.ctx.chat(embed=embed)


#
############
