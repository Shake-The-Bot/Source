############
#
from Classes.i18n import _
from discord import ui, PartialEmoji
from Classes import ShakeBot, ShakeContext, ShakeEmbed
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        embed = ShakeEmbed.default(self.ctx, 
            title=_("Pong! 🏓"), 
            
        )
        embed.add_field(
            name=_("Discord Gateway"), inline=True,
            value='> **{}**ms'.format(round(self.bot.latency * 1000))
        )
        embed.add_field(
            name=_("Client Latency"), inline=True,
            value='> **{}**ms'.format(0)
        )
        await self.ctx.smart_reply(embed=embed, view=Link('https://discordstatus.com/'))

class Link(ui.View):
    def __init__(self, link):
        super().__init__()
        self.add_item(
            ui.Button(
                emoji=PartialEmoji(name='\N{PERSONAL COMPUTER}',),
                label=_("Discord Status"), url=link,
            )
        )
#
############