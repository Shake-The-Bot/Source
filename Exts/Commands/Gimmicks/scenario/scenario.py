############
#
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from random import choice
from .utils.wwyds import whatyoudo
from Classes.i18n import _, current
########
#
class command():
    def __init__(self, ctx):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot

    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx, )
        embed.set_author(name='Shake', icon_url=self.bot.user.avatar.url)
        embed.title = _("Put yourself to the test! What would you do and why ?")
        question = _(choice(list(whatyoudo)))
        embed.description = '>>> {}'.format(question)
        embed.add_field(name='\u200b', value=self.ctx.bot.config.embed.footer, inline=False)
        return await self.ctx.smart_reply(embed=embed)