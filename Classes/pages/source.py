############
#
from Classes.i18n import _
from Classes.useful import MISSING
from Classes.exceptions import NothingHereYet
from discord import File, Guild, Interaction
from discord.ext import menus
from Classes.pages import page
from typing import Optional, Any, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from Classes import ShakeBot, ShakeEmbed, ShakeContext
else:
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot
    from discord import Embed as ShakeEmbed

class ItemsPageSource(menus.PageSource):
    def is_paginating(self) -> bool: 
        return True
    
    def get_max_pages(self) -> Optional[int]:
        return 1

    async def get_page(self, page: int) -> Any:
        self.page = page
        return self

    def format_page(self, menu: page.menus, items: Any) -> Tuple[ShakeEmbed, File]:
        raise NothingHereYet


class ListPageSource(menus.ListPageSource):
    def __init__(
            self, ctx: Union[ShakeContext, Interaction], items: list[Any], title: str, group: Optional[Any] = MISSING, description: str = MISSING, 
            paginating: bool = True, per_page: Optional[int] = 6, *args, **kwargs
        ):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.group: Any = group
        self.items: list[Any] = items
        self.title: str = title
        self.description: Optional[str] = description
        self.paginating = paginating
        self.args = args
        self.kwargs = kwargs
        super().__init__(entries=items, per_page=per_page)

    def add_field(self, embed: ShakeEmbed, item: Any):
        if not hasattr(item, 'name') or not hasattr(item, 'value'):
            raise NothingHereYet
        embed.add_field(name=item.name, value=item.value)
    
    def is_paginating(self) -> bool:
        return self.paginating

    async def format_page(self, menu: page.menus, items: list[Guild]):
        file = None
        maximum = self.get_max_pages()
        details = (f' (Page {menu.page + 1} / {maximum})') if maximum > 1 else ''
        title = self.title + (details if self.description else '')
        description = self.description if self.description else '**'+details+'**'
        embed = ShakeEmbed(colour=self.bot.config.embed.colour, title=title, description=description)
        for item in items:
            self.add_field(embed, item)
        return embed, file

class FrontPageSource(menus.PageSource):
    index: int

    def is_paginating(self) -> bool:
        raise NothingHereYet

    def get_max_pages(self) -> Optional[int]:
        raise NothingHereYet

    async def get_page(self, index: int) -> Any:
        raise NothingHereYet

    def format_page(self, menu: page.menus, page: Any) -> Tuple[ShakeEmbed, File]: 
        raise NothingHereYet
#
############