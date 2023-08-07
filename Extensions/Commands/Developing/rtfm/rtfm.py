############
#
from __future__ import annotations

from asyncio import create_task, gather
from difflib import get_close_matches
from typing import TYPE_CHECKING, Any, List, NamedTuple, Optional, Union

from bs4 import BeautifulSoup
from discord import Interaction
from discord.ui import Select
from discord.utils import escape_markdown

from Classes import Format, ShakeBot, ShakeCommand, ShakeContext, ShakeEmbed, _
from Classes.accessoires import (
    CategoricalMenu,
    ItemPageSource,
    ListPageSource,
    ShakePages,
)
from Classes.helpful import ShakeContext
from Classes.types import DocItem, Modules

if TYPE_CHECKING:
    from . import rtfm_extension


class SearchItem(NamedTuple):
    name: str
    link: str


class command(ShakeCommand):
    def __init__(self, ctx: ShakeContext) -> None:
        super().__init__(ctx)
        self.cog: rtfm_extension = ctx.bot.get_cog("rtfm_extension")

    async def __await__(self, module: Modules, search: Optional[str]):
        assert bool(self.bot.cache["symbols"])

        if search is None:
            embed = ShakeEmbed(
                timestamp=None,
                description=Format.blockquotes(Format.bold(module.value)),
            )
            return await self.ctx.chat(embed=embed)

        symbols = self.cog.symbols.get(module.name)
        assert symbols

        await self.bot.pool.execute(
            "INSERT INTO rtfm (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET count = rtfm.count + 1;",
            self.ctx.author.id,
        )

        matches = get_close_matches(search, list(symbols))

        select = SymbolSelect(self.ctx, source=SymbolSource, cog=self.cog)
        select.items = [symbols[match] for match in matches]

        items = {id.lower(): item for id, item in symbols.items()}
        named = {
            item.name.lower(): item for item in symbols.values() if item.id != item.name
        }
        source = None

        if item := items.get(search.lower()):
            source = SymbolSource(self.ctx, item)
        elif item := named.get(search.lower()):
            source = SymbolSource(self.ctx, item)
        else:
            if bool(matches):
                source = SearchSource(
                    self.ctx,
                    searches=[
                        SearchItem(symbols[match].name, symbols[match].url)
                        for match in matches
                    ],
                )
        if source:
            menu = SymbolMenu(
                ctx=self.ctx,
                source=source,
                select=select,
                cog=self.cog,
                symbols=symbols,
                module=module,
                search=search,
            )
            if not await menu.setup():
                raise
            return await menu.send(ephemeral=True)
        else:
            return await self.ctx.chat(_("Couldn't find anything."))

    async def rtfms(self):
        source = SearchSource(
            self.ctx,
            searches=[SearchItem(module.name, module.value) for module in Modules],
        )

        menu = ShakePages(source, self.ctx)
        if not await menu.setup():
            raise
        return await menu.send(ephemeral=True)


class SymbolMenu(CategoricalMenu):
    symbols: dict[Modules, dict[str, DocItem]]
    module: Modules
    search: str

    def __init__(
        self,
        cog: rtfm_extension,
        symbols: dict[Modules, dict[str, DocItem]],
        module: Modules,
        search: str,
        select: SymbolSelect,
        **kwargs,
    ):
        super().__init__(select=None, **kwargs)
        self.cog = cog
        self.symbols = symbols
        self.module = module
        self.search = search

        self.clear_items()
        self.add_item(select())
        self.fill()


class SymbolSelect(Select):
    view: SymbolMenu

    def __init__(self, ctx: ShakeContext, source: SymbolSource, cog: rtfm_extension):
        super().__init__(
            placeholder=_("Choose a symbol..."),
            min_values=1,
            max_values=1,
            row=0,
        )
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.cog: rtfm_extension = cog
        self.source: SymbolSource = source
        self.__items: list[DocItem] = None

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        create_task(self.__fill_options())
        return self

    @property
    def items(self) -> list[DocItem]:
        return self.__items

    @items.setter
    def items(self, matches: Any):
        self.__items = matches
        if not bool(matches):
            self.disabled = True
            self.placeholder = _("No symbols to choose...")

    async def __fill_options(self) -> None:
        assert self.items is not None
        fetches = list()
        for item in self.items:
            self.add_option(label=item.name, value=item.id)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        item = self.view.symbols.get(self.values[0])
        assert item

        source = SymbolSource(ctx=self.ctx, item=item)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()
        await self.view.rebind(source=source, interaction=interaction)


class SearchSource(ListPageSource):
    items: List[DocItem]

    def __init__(self, ctx, searches: List[SearchItem]):
        super().__init__(ctx=ctx, title=None, items=searches, per_page=8)

    async def format_page(self, menu: SymbolMenu, items: List[SearchItem]):
        description = str()
        for name, link in items:
            name = Format.codeblock(name)
            description += Format.list(Format.hyperlink(name, link)) + "\n"

        embed = ShakeEmbed(
            description=description,
        )

        return embed, None


class SymbolSource(ItemPageSource):
    item: DocItem

    def __init__(self, ctx: ShakeContext, item: DocItem):
        super().__init__(ctx=ctx, item=item, paginating=False)

    async def get_page(self, page: DocItem) -> "SymbolSource":
        self.page: DocItem = page
        return self

    async def format_page(self, menu: SymbolMenu, *args: Any, **kwargs: Any):
        await self.ctx.defer()
        embed = ShakeEmbed(
            title=escape_markdown(self.item.id),
            url=self.item.url,
            description=await menu.cog.get_markdown(self.item),
        )
        embed.set_author(
            name=self.item.module.name.capitalize(), url=self.item.module.value
        )
        return embed, None


#
############
