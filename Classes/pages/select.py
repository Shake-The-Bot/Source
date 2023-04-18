
from discord import ui, PartialEmoji, Interaction, utils
from Classes.pages.source import FrontPageSource, ListPageSource
from typing import Any, TYPE_CHECKING
from Classes.i18n import _
Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeContext, ShakeBot
else:
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot

class CategoricalSelect(ui.Select):
    def __init__(self, ctx: ShakeContext, categories: dict[Group, list[Item]], source: ListPageSource):
        super().__init__(placeholder=_("Choose a Category..."), min_values=1, max_values=1, row=0,)
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.source: ListPageSource = source
        self.categories: dict[Group, list[Item]] = categories
        self.__fill_options()


    def __fill_options(self) -> None:
        self.add_option(label=_("Back"), emoji=PartialEmoji(name='left', id=1033551843210579988), value="mainmenu")
        for Group in self.categories.keys():
            name = getattr(Group, 'qualified_name', str(Group))
            description = getattr(Group, 'description', '').split("\n", 1)[0] or None
            emoji = getattr(Group, "display_emoji", None)
            label = getattr(Group, "label", None)
            self.add_option(label=label, value=name, description=None, emoji=emoji) # description=description, 


    async def callback(self, interaction: Interaction):
        assert self.view is not None
        value = self.values[0]
        if value == "mainmenu":
            if isinstance(self.view.source, FrontPageSource):
                if self.view.current_page == 0:
                    await utils.maybe_coroutine(self.view.stop)
                    return
            await self.view.rebind(self.view.front(), interaction)
        else:
            category = self.bot.get_cog(value)
            if category is None: 
                return await interaction.response.send_message(_("This category does not exist."), ephemeral=True)
            items = self.categories[category]
            if not items:     
                return await interaction.response.send_message(_("This category has no items for you."), ephemeral=True)
            source = self.source(ctx=self.ctx, group=category, items=items, interaction=interaction)
            self.view.current_source = self.view.current_page = None
            await self.view.rebind(source, interaction)
