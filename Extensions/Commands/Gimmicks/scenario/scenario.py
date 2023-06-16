############
#
from random import choice

from Classes import ShakeCommand, ShakeEmbed, _

from .utils.wwyds import whatyoudo


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        embed.set_author(name="Shake", icon_url=self.bot.user.avatar.url)
        embed.title = _("Put yourself to the test! What would you do and why ?")
        question = _(choice(list(whatyoudo)))
        embed.description = ">>> {}".format(question)
        embed.advertise(self.bot)
        return await self.ctx.chat(embed=embed)
