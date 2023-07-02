from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

from discord import ButtonStyle, File, Interaction, PartialEmoji, ui
from discord.ext import menus

from Classes import MISSING, ShakeContext, ShakeEmbed, TextFormat, _
from Classes.accessoires import page

if TYPE_CHECKING:
    from Classes.accessoires import ForwardingMenu
    from Classes.helpful import ShakeBot, ShakeContext

__all__ = (
    "SourceSource",
    "FrontPageSource",
    "ItemPageSource",
    "ForwardingSource",
    "ForwardingFinishSource",
    "ListPageSource",
)

############
#


class SourceSource(menus.PageSource):
    group: SourceTypes

    def __init__(self, ctx: ShakeContext, group, **kwargs) -> None:
        super().__init__()
        self.ctx = ctx
        self.group = group

    def is_paginating(self) -> bool:
        return self.group.is_paginating()

    def get_max_pages(self) -> Optional[int]:
        return self.group.get_max_pages()

    async def get_page(self, page: int) -> Any:
        return await self.group.get_page(page)

    def format_page(self, *args: Any, **kwargs: Any) -> Tuple[ShakeEmbed, File]:
        return self.group.format_page(*args, **kwargs)


class ItemPageSource(menus.PageSource):
    def __init__(
        self,
        ctx: ShakeContext | Interaction,
        item: Optional[Any] = MISSING,
        label: Optional[str] = MISSING,
        title: Optional[str] = MISSING,
        description: Optional[str] = MISSING,
        *args,
        **kwargs,
    ):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.item: Any = item
        self.title: str = title
        self.description: Optional[str] = description
        self.__label = label or title
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    @property
    def label(self) -> str:
        return self.__label

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="dot", id=1093146860182568961)

    def is_paginating(self) -> bool:
        return True

    def get_max_pages(self) -> Optional[int]:
        return 1

    @property
    def maximum(self) -> int:
        return 1

    async def get_page(self, page: int) -> Any:
        return self

    def format_page(self, menu: page.menus, item: Any) -> Tuple[ShakeEmbed, File]:
        raise NotImplemented


class ListPageSource(menus.ListPageSource):
    def __init__(
        self,
        ctx: ShakeContext | Interaction,
        items: List[Any],
        title: str,
        group: Optional[Any] = MISSING,
        description: Optional[str] = MISSING,
        paginating: bool = True,
        per_page: Optional[int] = 6,
        label: Optional[str] = MISSING,
        *args,
        **kwargs,
    ):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.group: Any = group
        self.items: List[Any] = items
        self.title: str = title or getattr(group, "title", MISSING)
        self.description: Optional[str] = description
        self.paginating = paginating
        self.args = args
        self.kwargs = kwargs
        self.__label = label or title
        super().__init__(entries=list(items), per_page=per_page)

    def add_field(self, embed: ShakeEmbed, item: Any | Tuple[Any, Any]):
        if isinstance(item, tuple):
            embed.add_field(name=item[0], value=item[1])
            return
        if hasattr(item, "name") and hasattr(item, "value"):
            embed.add_field(name=item.name, value=item.value)
            return
        raise NotImplemented

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="dot", id=1093146860182568961)

    @property
    def label(self) -> str:
        return self.__label

    @property
    def maximum(self) -> int:
        return 1 if self.get_max_pages() == 0 else self.get_max_pages()

    def is_paginating(self) -> bool:
        return self.paginating

    async def format_page(self, menu: page.menus, items: list[Any]):
        file = None
        details = (f" 〈 {menu.page + 1} / {self.maximum} 〉") if self.maximum > 1 else ""
        title = self.title + (details if self.description else "")
        description = (
            self.description
            if self.description
            else ("**" + details + "**" if details else "")
        )
        embed = ShakeEmbed().default(
            ctx=self.ctx,
            colour=self.bot.config.embed.colour,
            title=title,
            description=description,
        )
        for item in items:
            self.add_field(embed, item)
        return embed, file


class FrontPageSource(menus.PageSource):
    index: int

    def __call__(self, **kwargs: Any) -> Any:
        return self

    def is_paginating(self) -> bool:
        return True

    def get_max_pages(self) -> Optional[int]:
        return 1

    async def get_page(self, index: int) -> Any:
        self.index = index
        return self

    def format_page(self, menu: page.menus, page: Any) -> Tuple[ShakeEmbed, File]:
        raise NotImplemented


SourceTypes = ItemPageSource | ListPageSource | FrontPageSource
sources = (ItemPageSource, ListPageSource, FrontPageSource)


class ForwardingSource:
    view: ForwardingMenu
    bot: ShakeBot
    ctx: ShakeContext
    items: List[Union[ui.Select, ui.Button]]

    next: Optional[ForwardingSource]
    previous: Optional[ForwardingSource]

    def __init__(
        self,
        view: ForwardingMenu,
        previous: Optional[ForwardingSource],
        next: Optional[ForwardingSource],
        items: List[Union[ui.Select, ui.Button]],
    ) -> None:
        self.view = view
        self.bot = view.bot
        self.ctx = view.ctx
        self.items = items
        self.previous = previous
        self.next = next
        for item in items:
            if not item in (view.cancel, view.previous):
                item.callback = self.__call__

    async def message(self) -> dict:
        raise NotImplemented

    async def __call__(self, interaction: Interaction) -> None:
        value = self.item.values[0]
        await self.callback(interaction, value)

    async def callback(self, interaction: Interaction, value: Any) -> None:
        raise NotImplemented


class ForwardingFinishSource(ForwardingSource):
    item = ui.Button(label="Confirm and Finish", row=4, style=ButtonStyle.green)

    def __init__(self, view: ForwardingMenu) -> None:
        self.item.callback = self.__call__
        super().__init__(
            view=view,
            previous=None,
            next=None,
            items=[view.previous, self.item],
        )

    async def __call__(self, interaction: Interaction) -> None:
        await self.callback(interaction)

    async def callback(self, interaction: Interaction):
        self.view.stop()
        if not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed(timestamp=None)
        embed.description = TextFormat.bold(
            _("Please confirm your selection to exit the menu.")
        )
        return {"embed": embed}


#
############
