############
#
from typing import Optional

from discord import Member
from discord.ext.commands import Greedy

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(
        self, ctx: ShakeContext, member: Greedy[Member], reason: Optional[str]
    ):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.member: Greedy[Member] = member
        self.reason: Optional[str] = reason or _("No reason provided")

    async def __await__(self):
        try:
            for member in self.member:
                await member.kick(
                    reason="kick command executed by {author}: {reason}".format(
                        author=self.ctx.author, reason=self.reason
                    )
                )
        except Exception as error:
            raise error
        else:
            embed = ShakeEmbed.default(
                self.ctx,
                description=_(
                    "{emoji} {prefix} The specified members were successfully kicked"
                ).format(emoji=self.bot.emojis.cross, prefix=self.bot.emojis.prefix),
            )
            await self.ctx.chat(embed=embed)
        finally:
            return


#
############
