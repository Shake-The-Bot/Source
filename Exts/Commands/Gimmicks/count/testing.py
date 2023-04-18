############
#
from discord import ui, ButtonStyle, Interaction
from Classes.i18n import _
from Classes import ShakeContext, ShakeBot
########
#
class command():
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        await self.ctx.smart_reply(_("Start?"), view=EphemeralCounter())

class Counter(ui.View):
    @ui.button(label='0', style=ButtonStyle.grey)
    async def count(self, interaction: Interaction, button: ui.Button):
        number = int(getattr(button, 'label', 0))
        button.label = str(number + 1)
        if number + 1 >= 100:
            button.style = ButtonStyle.green
            button.label = _("Congratulation")
            button.disabled = True
        await interaction.response.edit_message(view=self)


class EphemeralCounter(ui.View):
    @ui.button(label=_("Yes"), style=ButtonStyle.blurple)
    async def receive(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(_("Have fun!"), view=Counter(), ephemeral=True)
#
############