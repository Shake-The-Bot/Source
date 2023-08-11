############
#
from discord import ButtonStyle, Interaction, Message, ui

from Classes import ShakeCommand, ShakeContext, _


########
#
class command(ShakeCommand):
    async def __await__(self):
        menu = Counter(ctx=self.ctx)
        await menu.send()


class Counter(ui.View):
    message: Message

    def __init__(self, ctx: ShakeContext):
        self.ctx = ctx
        super().__init__()

    async def on_timeout(self) -> None:
        self.count.disabled = True
        await self.message.edit(view=self)

    async def send(self):
        self.message = await self.ctx.chat(_("Have fun!"), view=self, ephemeral=True)

    @ui.button(label="0", style=ButtonStyle.grey)
    async def count(self, interaction: Interaction, button: ui.Button):
        number = int(button.label)
        button.label = str(number + 1)
        await interaction.response.edit_message(view=self)


#
############
