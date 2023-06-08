from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from discord import ButtonStyle, Interaction, ui
from discord.ext import menus

from Classes.pages import source as _source
from Classes.pages.page import ShakePages
from Classes.pages.select import CategoricalSelect
from Classes.pages.source import FrontPageSource, ItemPageSource, ListPageSource

__all__ = ("ListMenu", "CategoricalMenu", "LinkingSource")

Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeContext
    from Classes.types import sourcetypes


class JokerItems:
    pass


class LinkingSource:
    value: str
    source: menus.PageSource

    def __init__(self, source: menus.PageSource, **kwargs) -> None:
        self.source: menus.PageSource = source
        self.items: Dict[Any, Any | List[Any]] = dict()
        for k, v in kwargs:
            setattr(self, k, v)
        self.__await__()
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.items: Dict[Any, Any | List[Any]] = dict()
        self.__await__()
        return self

    def __await__(
        self,
    ):
        raise NotImplemented

    def __str__(self) -> str:
        raise NotImplemented

    @property
    def label(self) -> str:
        raise NotImplemented


class ListMenu(ShakePages):
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


class CategoricalMenu(ShakePages):
    def __init__(
        self,
        ctx: ShakeContext,
        source: menus.PageSource,
        select: CategoricalSelect,
        front: Optional[_source.FrontPageSource] = None,
        timeout: Optional[float] = 180.0,
        **kwargs: Any,
    ):
        super().__init__(source=source, ctx=ctx, timeout=timeout, **kwargs)
        self.select: CategoricalSelect = select
        self.__front: _source.FrontPageSource = front or source

    @property
    def front(
        self,
    ) -> _source.FrontPageSource:
        return self.__front

    @front.setter
    def front(self, value) -> None:
        self.__front = value

    async def rebind(
        self,
        source: menus.PageSource,
        page: Optional[int] = 0,
        interaction: Optional[Interaction] = None,
        update: Optional[bool] = True,
    ) -> None:
        self.source = source
        self.page = 0 if isinstance(source, _source.ItemPageSource) else page
        if update:
            self.update(self.page)
        await source._prepare_once()
        page_source = await source.get_page(page)
        self.kwargs, self.file = await self._get_from_page(page_source)

        if interaction or self.message:
            try:
                if (
                    not interaction
                    or not isinstance(interaction, Interaction)
                    or interaction.response.is_done()
                ):
                    if self.message:
                        await self.message.edit(
                            **self.kwargs,
                            attachments=(
                                self.file
                                if isinstance(self.file, list)
                                else [self.file]
                            )
                            if self.file
                            else [],
                            view=self,
                        )
                else:
                    await interaction.response.edit_message(
                        **self.kwargs,
                        attachments=(
                            self.file if isinstance(self.file, list) else [self.file]
                        )
                        if self.file
                        else [],
                        view=self,
                    )
            except:
                pass

    def add_categories(
        self, categories: Dict[Group | Any, List[Item] | sourcetypes]
    ) -> None:
        for key, value in dict(categories).items():
            source = isinstance(
                key,
                (
                    ItemPageSource,
                    ListPageSource,
                    FrontPageSource,
                ),
            )
            if source and value is None:
                continue
            if not bool(value) and not value == JokerItems:
                categories.pop(key)

        self.clear_items()
        self.select.categories = categories
        self.add_item(self.select())
        self.fill()

    async def on_timeout(self, interaction: Optional[Interaction] = None) -> None:
        await self.rebind(self.front(timeout=True), interaction=interaction)
        for item in self._children:
            if isinstance(item, ui.Button) or isinstance(item, ui.Select):
                item.disabled = True
                item.style = ButtonStyle.grey
        await self.rebind(
            self.front(timeout=True), interaction=interaction, update=False
        )
