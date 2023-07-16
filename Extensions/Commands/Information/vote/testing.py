############
#
from discord import File, PartialEmoji, ui

from Classes import ShakeCommand, ShakeEmbed, TextFormat, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
        )
        embed.title = _("> Help Shake on its way (Vote)")
        embed.add_field(
            inline=False,
            name=_("{emoji} The benefit of supporting Shake with Voting").format(
                emoji=self.bot.emojis.dot
            ),
            value=TextFormat.blockquotes(
                TextFormat.italics(
                    _(
                        "Supporting the Bot with a Vote will keep the motivation for the development of Shake, increases it's visibility and helps others discover Shake too."
                    )
                )
            ),
        )
        embed.add_field(
            inline=False,
            name=_("{emoji} Sites I am listed at").format(emoji=self.bot.emojis.dot),
            value=TextFormat.bold(
                """[Top.gg]({topgg})
                [Discordbotlist.com]({discordbotlist})
                [discord-botlist.eu]({botlisteu})
                [infinitybots.gg]({infinitybots})"""
            ).format(
                topgg=self.bot.config.other.topgg.vote,
                discordbotlist=self.bot.config.other.discordbotlist.vote,
                botlisteu=self.bot.config.other.botlisteu.vote,
                infinitybots=self.bot.config.other.infinitybots.vote,
            ),
        )

        embed.add_field(
            inline=False,
            name=_("{emoji} Other related links").format(emoji=self.bot.emojis.dot),
            value=TextFormat.bold(
                """[Discord Bots]({discordbots})
                [Discords]({discords})"""
            ).format(
                discordbots=self.bot.config.other.discordbots.link,
                discords=self.bot.config.other.discords.link,
            ),
        )
        file = File(fp="./Assets/shake/banner.png", filename="banner.png")
        embed.set_image(url="attachment://banner.png")
        return await self.ctx.chat(
            ephemeral=True, file=file, embed=embed, view=Button(self.bot)
        )


class Button(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=5)
        self.bot = bot
        button = ui.Button(
            emoji=PartialEmoji(animated=True, name="heartflow", id=952690616859512912),
            label=_("Vote for Shake"),
            url=self.bot.config.other.authentication,
        )
        self.add_item(button)


#
############
