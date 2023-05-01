############
#
from discord import Guild, ContentFilter, File
from Classes.i18n import _
from typing import Literal, Any, Optional, Tuple, Union
from discord.ext import menus
from Classes.pages import CategoricalMenu, CategoricalSelect, FrontPageSource, ItemsPageSource, ElseKwarg
from discord.utils import format_dt, maybe_coroutine
from Classes import ShakeBot, ShakeContext, ShakeEmbed
########
#
ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']
ctx_tick = lambda bot: (str(bot.emojis.cross), str(bot.emojis.hook))
########
#

class INFO(ElseKwarg):
    def __init__(self, guild: Guild) -> None:
        self.guild: Guild = guild
        super().__init__()


class Roles(INFO):
    def __await__(self):
        for role in self.guild.roles:
            self.items[role] = role.mention
    
    def __str__(self) -> str:
        return 'roles'

    @property
    def label(self) -> str: 
        return _("Roles")
            

class Assets(INFO):
    def __await__(self):
        if self.guild.icon:
            self.items[self.guild.icon] = self.guild.icon.url
        if self.guild.banner:
            self.items[self.guild.banner] = self.guild.banner.url
        if self.guild.splash:
            self.items[self.guild.splash] = self.guild.splash.url
    
    def __str__(self) -> str:
        return 'assets'
    
    @property
    def label(self) -> str: 
        return _("Avatar/Banner")


class Emojis(INFO):
    def __await__(self):
        for emoji in self.guild.emojis:
            self.items[emoji] = str(emoji)
    
    def __str__(self) -> str:
        return 'emojis'
    
    @property
    def label(self) -> str: 
        return _("Emojis")


class Channels(INFO):
    def __await__(self):
        for text_channel in self.guild.text_channels:
            self.items[text_channel.category] = text_channel.mention

        for voice_channel in self.guild.voice_channels:
            self.items[voice_channel.category] = voice_channel.mention

        for stage_channel in self.guild.stage_channels:
            self.items[stage_channel.category] = stage_channel.mention

        for forum in self.guild.forums:
            self.items[forum.category] = forum.mention

        for thread in self.guild.threads:
            self.items[thread.category] = thread.mention
    
    def __str__(self) -> str:
        return 'channels'
    
    @property
    def label(self) -> str: 
        return _("Channels/Threads")

features = Union[Roles, Assets, Emojis, Channels]


class command():
    def __init__(self, ctx: ShakeContext, guild: Guild):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.guild: Guild = guild

    async def __await__(self):

        source = Front()
        select = CategoricalSelect(self.ctx, source=Items)
        menu = Menu(ctx=self.ctx, source=source, guild=self.guild, select=select)

        menu.add_categories(roles=Roles(self.guild), assets=Assets(self.guild), emojis=Emojis(self.guild), channels=Channels(self.guild))
        
        if await menu.setup():
            await menu.send()


class Menu(CategoricalMenu):
    def __init__(
            self, ctx: ShakeContext, source: menus.PageSource, guild: Guild, 
            select: Optional[CategoricalSelect] = None, front: Optional[FrontPageSource] = None
        ):
        self.guild: Guild = guild
        super().__init__(ctx, source=source, select=select, front=front)

    def embed(self, embed: ShakeEmbed):
        recovery = 'https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png'
        embed.set_author(name=str(self.guild), icon_url=getattr(self.guild.icon, 'url', recovery))
        embed.set_thumbnail(url=getattr(self.guild.icon, 'url', recovery))
        return embed


class Items(ItemsPageSource):
    def __init__(self, ctx: ShakeContext, group: features, items: Any, **kwargs: Any) -> None:
        super().__init__()
        self.ctx = ctx
        self.group = group
        self.items = items
        self.kwargs = kwargs

    def is_paginating(self) -> bool: 
        return True
    
    def get_max_pages(self) -> Optional[int]:
        return 1

    async def get_page(self, item: int) -> Any:
        self.item = item
        return self

    def format_page(self, menu: Menu, items: Any) -> Tuple[ShakeEmbed, File]:
        guild = menu.guild
        # TODO
        # if isinstance(items, )


class Front(FrontPageSource):
    def __init__(self) -> None:
        super().__init__()

    def __call__(self, **kwargs: Any) -> Any:
        return self

    def is_paginating(self) -> bool: 
        return True

    def get_max_pages(self) -> Optional[int]: 
        return 1

    async def get_page(self, index: int) -> Any:
        self.index = index
        return self

    def format_page(self, menu: Menu, items: Any):
        guild = menu.guild
        embed = ShakeEmbed.default(menu.ctx, title=_("General Overview"))
        information = dict()


        information[_("Name")+':'] = (f'`{guild.name}`', False)

        information[_("IDentification")+':'] = f'`{guild.id}`'
        information[_("Created")+':'] = f'{format_dt(guild.created_at, style="F")}'
        information['1'] = None

        information[_("Owner")+':'] = f'`{guild.owner}`'
        information[_("Member(s)")+':'] = f'`{guild.member_count} ({len([member for member in guild.members if member.bot])} {_("Bots")})`'
        information['2'] = None


        for name, value in information.items():
            value, inline = (value[0], value[1]) if isinstance(value, tuple) else (value, True)
            embed.add_field(name=str(name) if not value is None else '\u200b', value=str(value) if not value is None else '\u200b', inline=inline)
    
        return embed, None