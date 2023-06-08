############
#
from datetime import timedelta
from typing import Optional

from discord import Member
from discord.ext.commands import Greedy

from Classes import DurationDelta, ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(self, ctx: ShakeContext, member, time, reason: Optional[str]):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.member: Greedy[Member] = member
        self.time: DurationDelta = time
        self.reason: Optional[str] = reason or _("No reason provided")

    async def __await__(self):
        # convert = {"s": 1, "m": 60, "h": 60*60, "d": 60*60*24, "w": 60*60*24*7}     #
        # time = int(self.time[0]) * convert[self.time[-1]]                           #    updated to Classes.converter.DurationDelta

        try:
            for member in self.member:
                await member.timeout(
                    until=timedelta(seconds=self.time),
                    reason="{reason} {author}".format(
                        reason=self.reason, author=self.ctx.author
                    ),
                )

        except Exception as error:
            raise error

        else:
            embed = ShakeEmbed.to_success(
                self.ctx, description=_("The specified members were successfully muted")
            )
            await self.ctx.chat(embed=embed)


#
############
