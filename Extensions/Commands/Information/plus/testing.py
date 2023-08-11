############
#
from discord import PartialEmoji, ui

from Classes import Format, ShakeCommand, ShakeEmbed, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
            title=_("> Shake Plus (Shake+)"),
            description=_(
                "{emoji} This Discord server has no premium activated."
            ).format(emoji=self.bot.assets.cross),
        )
        embed.add_field(
            inline=False,
            name=_("{emoji} The benefit of supporting Shake as Patreon").format(
                emoji=self.bot.assets.dot
            ),
            value=_(
                """Supporting the Bot as Patreon will keep the motivation for the development of Shake and make sure that all hosting costs are covered.

                Plus makes **voting no longer necessary** and gives you **more creator channel** to customize! 
                """
            ),
        )
        embed.add_field(
            inline=False,
            name=_("{emoji} Helpful links for understanding Patreon").format(
                emoji=self.bot.assets.dot
            ),
            value=Format.bold(
                _(
                    """[What is Patreon?](https://support.patreon.com/hc/articles/204606315-What-is-Patreon-)
                [What currencies does Patreon support?](https://support.patreon.com/hc/articles/360039589091-Patreon-s-supported-currencies)
                [How do I connect Discord to Patreon?](https://support.patreon.com/hc/articles/212052266-How-do-I-connect-Discord-to-Patreon-Patron-)"""
                )
            ),
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/949420891702427688/1004805116186071080/TempVoice_Premium_Banner.png"
        )
        return await self.ctx.chat(ephemeral=True, embed=embed, view=Button(self.bot))


class Button(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=5)
        self.bot = bot
        button = ui.Button(
            emoji=PartialEmoji(animated=True, name="heartflow", id=952690616859512912),
            label=_("Add Shake to your server"),
            url=self.bot.config.bot.authentication,
        )
        self.add_item(button)


#
############
