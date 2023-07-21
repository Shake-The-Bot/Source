############
#
from typing import Optional

from discord import Object

from Classes import Format, ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    def __init__(self, ctx, guild: Object):
        super().__init__(ctx)
        self.guild: Optional[Object] = guild

    async def __await__(self):
        if not (
            guild := self.bot.get_guild(self.guild)
            if not self.guild is None
            else self.ctx.guild
        ):
            embed = ShakeEmbed.to_error(
                description=Format.bold(_("The given server is not valid"))
            )
        else:
            try:
                await guild.leave()
            except:
                embed = ShakeEmbed.to_error(
                    description=Format.bold(_("leaving the guild raised an error"))
                )

            else:
                embed = ShakeEmbed.to_success(
                    description=Format.bold(_("I'll leave the given server"))
                )
        await self.ctx.chat(embed=embed)


#
############
