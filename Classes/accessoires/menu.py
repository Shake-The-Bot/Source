from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List, Optional

from discord import ButtonStyle, Embed, Interaction, Message, PartialEmoji, ui
from discord.ext import menus

from Classes.accessoires import source as _source
from Classes.accessoires.page import ShakePages
from Classes.accessoires.select import CategoricalSelect
from Classes.accessoires.source import FrontPageSource, ItemPageSource, ListPageSource
from Classes.i18n import _
from Classes.types import Format

__all__ = ("ListMenu", "CategoricalMenu", "LinkingSource", "ForwardingMenu")

previousemoji = PartialEmoji(name="left", id=1033551843210579988)
Group = Item = Any

if TYPE_CHECKING:
    from Classes import ShakeBot, ShakeContext
    from Classes.accessoires import ForwardingFinishSource, ForwardingSource
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
        front = self.front(timeout=True) if callable(self.front) else self.front
        await self.rebind(front, interaction=interaction)
        for item in self._children:
            if isinstance(item, ui.Button) or isinstance(item, ui.Select):
                item.disabled = True
                item.style = ButtonStyle.grey
        await self.rebind(front, interaction=interaction, update=False)


class ForwardingMenu(ui.View):
    ctx: ShakeContext
    message: Message
    source: ForwardingSource
    items: Dict[int, List[ui.Item]]
    slots: List[List[ui.Item]]

    def __init__(self, ctx):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.timeouted = False
        super().__init__()

    @property
    def page(self) -> int:
        return self.pages[0]

    def insert(self, site: List[ui.Item], index: Optional[int] = None):
        if index is None:
            i = (self.pages[0] + self.pages[1]) / 2
        else:
            i = (2 * index - 1) / 2
        self.items[i] = site
        pass

    async def setup(self, sources: List[ForwardingSource], **kwargs) -> None:
        for source in sources:
            if any(
                item.callback in (ui.Select.callback, ui.Button.callback)
                for item in source.items
            ):
                raise ValueError("Items are not configured!")

        self.items = {0: [self.start_menu, self.cancel]} | {
            source: source.items for source in sources
        }
        self.pages = deque(list(self.items.keys()))

        self.update()
        embed = Embed(
            colour=self.bot.config.embed.colour,
            description=Format.bold(
                _("Before continuing you must click on the Setup button.")
            ),
        )
        view = kwargs.pop("view", None)
        em = kwargs.pop("embed", None)
        self.message = await self.ctx.send(embed=embed, **kwargs, view=self)
        return self.message

    def update(self, rotation: Optional[int] = None) -> None:
        timeouted = self.timeouted

        if rotation:
            self.pages.rotate(-rotation)

        self.clear_items()
        for item in self.items[self.page]:
            self.add_item(item)

        if timeouted:
            for item in self._children:
                item.disabled = True
                if isinstance(item, ui.Button):
                    item.style = ButtonStyle.grey

    async def show_source(
        self, source: Optional[ForwardingSource] = None, rotation: Optional[int] = None
    ):
        if rotation:
            self.update(rotation)
            if not source:
                source = self.page
        self.source = source
        await self.message.edit(**source.message(), view=self)

    async def on_timeout(
        self, interaction: Optional[Interaction] = None
    ) -> Coroutine[Any, Any, None]:
        self.timeouted = True
        self.update(-list(self.items.keys()).index(self.page))

        embed = self.message.embeds[0]
        embed.description = Format.bold(_("The ShakeMenu was canceled due inactivity"))
        await self.message.edit(embed=embed, view=self)
        self.stop()

    @ui.button(label=_("Start"), style=ButtonStyle.blurple, row=4)
    async def start_menu(self, interaction: Interaction, button: ui.Button):
        await self.show_source(rotation=1)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @ui.button(emoji=previousemoji, style=ButtonStyle.blurple, row=4)
    async def previous(self, interaction: Interaction, button: ui.Button):
        if self.source.previous:
            await self.show_source(self.source.previous(view=self), -1)
        else:
            await self.show_source(self.source, rotation=0)

        if not interaction.response.is_done():
            await interaction.response.defer()

    @ui.button(label=_("Cancel"), style=ButtonStyle.red, row=4)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        if not interaction.response.is_done():
            await interaction.response.defer()

        self.timeouted = True
        self.pages = [0]
        self.update()

        embed = self.message.embeds[0]
        embed.description = Format.bold(_("The ShakeMenu was canceled"))
        await self.message.edit(embed=embed, view=self)

        self.stop()
