############
#
from Classes.i18n import _
from Classes.useful import MISSING
from Classes.exceptions import NothingHereYet
from discord import File, Interaction, PartialEmoji
from discord.ext import menus
from Classes.pages import page
from typing import Optional, Any, Tuple, TYPE_CHECKING, Union, Dict, List

if TYPE_CHECKING:
    from Classes import ShakeBot, ShakeEmbed, ShakeContext
else:
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot
    from discord import Embed as ShakeEmbed

class AnyPageSource(menus.PageSource):
    def is_paginating(self) -> bool: 
        raise NothingHereYet
    
    def get_max_pages(self) -> Optional[int]:
        raise NothingHereYet

    async def get_page(self, page: int) -> Any:
        self.page = page
        return self

    def format_page(self, menu: page.menus, items: Any) -> Tuple[ShakeEmbed, File]:
        raise NothingHereYet

class ItemPageSource(menus.PageSource):
    def __init__(
            self, ctx: Union[ShakeContext, Interaction], item: Any, title: str, description: str = '', 
            label: Optional[str] = MISSING, *args, **kwargs
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
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name='dot', id=1093146860182568961)

    def is_paginating(self) -> bool: 
        return True
    
    def get_max_pages(self) -> Optional[int]:
        return 1

    async def get_page(self, page: int) -> Any:
        self.page = page
        return self

    def format_page(self, menu: page.menus, item: Any) -> Tuple[ShakeEmbed, File]:
        raise NothingHereYet


class ListPageSource(menus.ListPageSource):
    def __init__(
            self, ctx: Union[ShakeContext, Interaction], items: List[Any], title: str, group: Optional[Any] = MISSING, description: str = '', 
            paginating: bool = True, per_page: Optional[int] = 6, label: Optional[str] = MISSING, *args, **kwargs
        ):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.group: Any = group
        self.items: List[Any] = items
        self.title: str = title
        self.description: Optional[str] = description
        self.paginating = paginating
        self.args = args
        self.kwargs = kwargs
        self.__label = label or title
        super().__init__(entries=items, per_page=per_page)

    def add_field(self, embed: ShakeEmbed, item: Union[Any, Tuple[Any, Any]]):
        if isinstance(item, tuple):
            embed.add_field(name=item[0], value=item[1])
            return
        if hasattr(item, 'name') and hasattr(item, 'value'):
            embed.add_field(name=item.name, value=item.value)
            return
        raise NothingHereYet
    
    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name='dot', id=1093146860182568961)

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
        details = (f' 〈 {menu.page + 1} / {self.maximum} 〉') if self.maximum > 1 else ''
        title = self.title + (details if self.description else '')
        description = self.description if self.description else '**'+details+'**'
        embed = ShakeEmbed(colour=self.bot.config.embed.colour, title=title, description=description)
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
        raise NothingHereYet

sources = (ItemPageSource, ListPageSource, FrontPageSource)
Sources = Union[ItemPageSource, ListPageSource, FrontPageSource]
#
############