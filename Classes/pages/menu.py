
from discord.ext import menus
from Classes.pages import source as _source, select as _select, page
from typing import Any, Optional, TYPE_CHECKING
from discord import ui, ButtonStyle, Interaction
Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeContext
else:
    from discord.ext.commands import Context as ShakeContext

class ListMenu(page.Pages):
    def __init__(self, source: _source.ListPageSource, ctx: ShakeContext):
        super().__init__(source, ctx=ctx)

    async def rebind(self, source: menus.PageSource, interaction: Interaction) -> None:
        self.source = source
        self.page = 0
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_from_page(page)
        self.update(0)
        await interaction.response.edit_message(**kwargs, view=self)


class CategoricalMenu(page.Pages):
    def __init__(
            self, ctx: ShakeContext, 
            source: menus.PageSource,
            select: Optional[_select.CategoricalSelect] = None, 
            selectsource: Optional[_source.ListPageSource] = None,
            front: Optional[_source.FrontPageSource] = None, 
            **kwargs: Any
        ):
        super().__init__(source=source, ctx=ctx, **kwargs)
        self.select: _select.CategoricalSelect = select or _select.CategoricalSelect
        self.selectsource: _source.ListPageSource = selectsource 
        self.front: _source.FrontPageSource = front or source


    async def rebind(self, source: menus.PageSource, interaction: Optional[Interaction] = None, item: Optional[int] = 0, update: Optional[bool] = True) -> None:
        self.source = source
        self.page = 0 if isinstance(source, _source.ItemPageSource) else item
        if update:
            self.update(self.page)
        await source._prepare_once()
        page_source = await source.get_page(item)
        self.kwargs, self.file = await self._get_from_page(page_source)
        
        if interaction or self.message:
            if not interaction or not isinstance(interaction, Interaction) or interaction.response.is_done():
                if self.message:
                    await self.message.edit(**self.kwargs, attachments=(self.file if isinstance(self.file, list) else [self.file]) if self.file else [], view=self)
            else:
                await interaction.response.edit_message(**self.kwargs, attachments=(self.file if isinstance(self.file, list) else [self.file]) if self.file else [], view=self)
        await self.hear()


    def add_categories(self, categories: dict[Group, list[Item]]) -> None:
        if not bool(categories):
            return
        for group, items in categories.items():
            if bool(items):
                continue
            categories.pop(group, None)
        self.categories = categories
        self.clear_items()
        select = self.select(self.ctx, categories, self.selectsource)
        self.add_item(select)
        self.fill()


    async def on_timeout(self, interaction: Optional[Interaction] = None) -> None:
        await self.rebind(self.front(timeout=True), interaction=interaction)
        for item in self._children:
            if isinstance(item, ui.Button) or isinstance(item, ui.Select):
                item.disabled = True
                item.style = ButtonStyle.grey
        await self.rebind(self.front(timeout=True), interaction=interaction, update=False)
