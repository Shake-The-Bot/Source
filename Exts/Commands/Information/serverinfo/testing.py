############
#
from discord import (
    Guild, ContentFilter, File, Interaction, Member,
    PartialEmoji, Role, Asset, Emoji, Colour,
    CategoryChannel, VoiceChannel, StageChannel, ForumChannel, TextChannel, Thread
)
from Classes.i18n import _
from discord.enums import Status
from discord.activity import ActivityTypes, ActivityType
from inspect import cleandoc
from typing import Literal, Any, Optional, Tuple, Union, List, Dict
from discord.ext import menus
from Classes.pages import (
    CategoricalMenu, CategoricalSelect, AnyPageSource, 
    FrontPageSource, ListPageSource, ItemPageSource
)
from collections import Counter
from discord.utils import format_dt, maybe_coroutine
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from Classes.useful import MISSING, human_join, TextFormat
code = TextFormat.codeblock
mlcode = TextFormat.mlcb
bold = TextFormat.bold
########
#
ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']
VocalGuildChannel = Union[VoiceChannel, StageChannel]
GuildChannel = Union[VocalGuildChannel, ForumChannel, TextChannel, Thread]
ctx_tick = lambda bot: (str(bot.emojis.cross), str(bot.emojis.hook))
########
#

class command():
    def __init__(self, ctx: ShakeContext, guild: Guild):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.guild: Guild = guild

    def channelinfo(self,) -> Dict[str, str]:
        information = dict()
        emojis = (self.bot.emojis.hook, self.bot.emojis.cross)
        information[_("Categories")+':'] = '`'+ str((len(self.guild.categories))) +'`'
        information[_("Text Channels")+':'] = '`'+ str(len([channel for channel in self.guild.text_channels if channel.is_news])) +'`'
        information[_("Voice Channels")+':'] = '`'+ str(len(self.guild.voice_channels)) +'`'
        information[_("Stages")+':'] = '`'+ str(len(self.guild.stage_channels)) +'`'
        information[_("Forums")+':'] = '`'+ str(len(self.guild.forums)) +'`'
        information[_("Threads")+':'] = '`'+ str(len(self.guild.threads)) +'`'
        information[_("Rules Channel")+':'] =  emojis[bool(self.guild.rules_channel)]
        information[_("Announcements")+':'] = '`'+ str(len([channel for channel in self.guild.text_channels if not channel.is_news])) +'`'
        return information
    
    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=ServerItems)
        menu = Menu(ctx=self.ctx, source=Front(), guild=self.guild, select=select)

        menu.add_categories(
            categories={
                RolesSource(ctx=self.ctx, guild=self.guild): set(self.guild.roles), 
                AssetsSource(ctx=self.ctx, guild=self.guild): set(self.guild.emojis),
                EmojisSource(ctx=self.ctx, guild=self.guild): [self.guild.icon, self.guild.banner, self.guild.splash, self.guild.discovery_splash],
                ChannelsSource(ctx=self.ctx, guild=self.guild): set(self.guild.channels),
                MembersSource(ctx=self.ctx, guild=self.guild): set(self.guild.members),
                ActivitiesSource(ctx=self.ctx, guild=self.guild): set(m.activities for m in self.guild.members),
                PremiumSource(ctx=self.ctx, guild=self.guild): set(self.guild.premium_subscribers)
            }
        )
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
        embed.set_author(name=self.guild.name, icon_url=getattr(self.guild.icon, 'url', recovery))
        return embed


class RolesSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        roles: List[Role] = sorted([role for role in guild.roles if not role == guild.default_role], reverse=True)
        super().__init__(ctx, items=roles, title=MISSING, label=_("Roles"), paginating=True, per_page=6, *args, **kwargs)

    def format_page(self, menu: Menu, items: List[Role], **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Roles"))
        for role in items:
            i = self.items.index(role)+1
            ii = items.index(role)+1
            to_long = len(role.name) > 20
            name = '@'+(role.name[0:15]+'[...]' if to_long else role.name)
            member = menu.ctx.author in self.guild.members
            infos = {
                'ID:': f'{code(role.id)}', 
                _("Created")+':': str(format_dt(role.created_at, 'f')), 
                _("Mention")+':': role.mention if member else '@'+role.name,
                _("Colour")+':': code(str(role.colour)) if not role.colour == Colour.default() else _("Default")
            }
            text = '\n'.join(f'**{key}** {value}' for key, value in infos.items())
            embed.add_field(name=f'` {i}. ` ' + name, value=text, inline=True)
            if ii%2==0:
                embed.add_field(name=f'\u200b', value='\u200b', inline=True)
        embed.set_footer(text=_('Page {page}/{pages} (Total of {items} Roles)').format(page=menu.page + 1, pages=self.maximum, items=len(self.items)))
        return embed


class AssetsSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        self.from_dict: dict[Asset, str] = {
            guild.icon: _("Server's Icon"), guild.banner: _("Server's Banner"), 
            guild.splash: _("Server's Invite Splash"), guild.discovery_splash: _("Server's Discovery Splash")
        }
        super().__init__(ctx, items=list(x for x in self.from_dict.keys() if x), title=MISSING, label=_("Avatar/Banner"), paginating=True, per_page=1, *args, **kwargs)

    def format_page(self, menu: Menu, items: Asset,  **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Asset"))
        embed.set_image(url=items.url)
        embed.set_footer(text=_('Page {page} of {pages}').format(page=menu.page + 1, pages=self.maximum))
        return embed


class EmojisSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        emojis: List[Emoji] = sorted(guild.emojis, key=lambda e: e.animated, reverse=True)
        super().__init__(ctx, items=emojis, title=MISSING, label=_("Emojis"), paginating=True, per_page=8, *args, **kwargs)

    def format_page(self, menu: Menu, items: List[Emoji], **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Emojis"))
        for emoji in items:
            i = self.items.index(emoji)+1
            ii = items.index(emoji)+1
            infos = {
                'ID:': f'{code(emoji.id)}', 
                _("Created")+':': str(format_dt(emoji.created_at, 'f')), 
                _("Twitch")+'?': _("Yes") if emoji.managed else _("No"),
                _("Added")+':': emoji.user.mention if emoji.user in self.guild.members else emoji.user
            }
            text = '\n'.join(f'**{key}** {value}' for key, value in infos.items() if all([key is not None, value is not None]))
            embed.add_field(name=str(emoji), value=text)
            if ii%2==0:
                embed.add_field(name=f'\u200b', value='\u200b', inline=True)
        embed.set_footer(text=_('Page {page} of {pages} (Total of {items} Emojis)').format(page=menu.page + 1, pages=self.maximum, items=len(self.items)))
        return embed

class PremiumSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        subscriber: List[Member] = set(guild.premium_subscribers)
        super().__init__(ctx, items=subscriber, title=MISSING, label=_("Nitro Booster"), paginating=True, per_page=25, *args, **kwargs)

    def format_page(self, menu: Menu, items: List[Member], **kwargs: Any) -> ShakeEmbed:
        description = ', '.join([m.mention if self.ctx.author in self.guild.members else str(m) for m in items]) or ''
        embed = ShakeEmbed(title=_("Server Nitro Booster"), description=description)

        embed.set_footer(text=_('Page {page} of {pages} (Total of {items} Booster)').format(page=menu.page + 1, pages=self.maximum, items=len(self.entries)))
        return embed

class ChannelsSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        channels: List[GuildChannel] = sorted(
            filter(
                lambda channel: not isinstance(channel, CategoryChannel), 
                [channel for channel in guild.channels]
            ), key= lambda channel: channel.position
        )
        self.categories = sorted(set(channel.category for channel in channels), key=lambda category: getattr(category, 'position', -1))
        super().__init__(ctx, items=channels, title=MISSING, label=_("Channels"), paginating=True, per_page=25, *args, **kwargs)

    def format_page(self, menu: Menu, items: List[GuildChannel], **kwargs: Any) -> ShakeEmbed:
        categories, voices, stages, texts, forums, threads = (
            len(self.guild.categories), len(self.guild.stage_channels), len(self.guild.stage_channels), 
            len(self.guild.text_channels), len(self.guild.forums), len(self.guild.threads)
        )

        description = _("{categories} Categorie-, {voices} Voice-, {stages} Stage-, {forums} Forum- and {texts} Textchannel with {threads} Threads").format(
            categories=bold(categories), voices=bold(voices), stages=bold(stages), forums=bold(forums), texts=bold(texts), threads=bold(threads)
        )
        embed = ShakeEmbed(title=_("Server Channels"), description=description)

        categories = sorted(set(channel.category for channel in items), key=lambda category: getattr(category, 'position', -1))
        summedup = {
            category: [channel for channel in items if channel.category == category]
                for category in categories
        }
        
        for category in summedup.keys():
            i = self.categories.index(category) + 1
            channels = sorted(summedup[category], key=lambda channel: channel.position)
            value = human_join(list(channel.mention for channel in channels))
            if not menu.ctx.author in self.guild.members:
                value = human_join(list('#'+channel.name for channel in channels))
            embed.add_field(name=f'` {i}. ` ' + '#'+(category.name if category else _("NO CAT")), value=value, inline=False)

        embed.set_footer(text=_('Page {page} of {pages} (Total of {items} Channels)').format(page=menu.page + 1, pages=self.maximum, items=len(self.entries)))
        return embed

class MembersSource(ItemPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        super().__init__(ctx, item=guild.members, title=MISSING, label=_("Members"), paginating=True, per_page=25, *args, **kwargs)

    def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        members: List[Member] = self.item
        embed = ShakeEmbed(title=_("Server Members"))
        emojis = self.bot.emojis.status
        member = PartialEmoji(name='\N{BUSTS IN SILHOUETTE}')
        human = PartialEmoji(name='\N{BUST IN SILHOUETTE}')
        bot = PartialEmoji(name='\N{ROBOT FACE}')
        infos = {
                str(member) +' '+ _("Total Members"): mlcode(len(members)), 
                str(human) +' '+ _("Total Humans"): mlcode(len([m for m in members if not m.bot])), 
                str(bot) +' '+ _("Total Bots"): mlcode(len([m for m in members if m.bot])), 
                
                str(emojis.online) +' '+ _("Total Online"): mlcode(len([m for m in members if m.status == Status.online])), 
                str(emojis.online) +' '+ _("Humans Online"): mlcode(len([m for m in members if not m.bot and m.status == Status.online])), 
                str(emojis.online) +' '+ _("Bots Online"): mlcode(len([m for m in members if m.bot and m.status == Status.online])), 
                
                str(emojis.idle) +' '+ _("Total Idle"): mlcode(len([m for m in members if m.status == Status.idle])), 
                str(emojis.idle) +' '+ _("Humans Idle"): mlcode(len([m for m in members if not m.bot and m.status == Status.idle])), 
                str(emojis.idle) +' '+ _("Bots Idle"): mlcode(len([m for m in members if m.bot and m.status == Status.idle])), 
                
                str(emojis.dnd) +' '+ _("Total DND"): mlcode(len([m for m in members if m.status == Status.dnd])), 
                str(emojis.dnd) +' '+ _("Humans DND"): mlcode(len([m for m in members if not m.bot and m.status == Status.dnd])), 
                str(emojis.dnd) +' '+ _("Bots DND"): mlcode(len([m for m in members if m.bot and m.status == Status.dnd])), 
                
                str(emojis.offline) +' '+ _("Total Offline"): mlcode(len([m for m in members if m.status == Status.offline])), 
                str(emojis.offline) +' '+ _("Humans Offline"): mlcode(len([m for m in members if not m.bot and m.status == Status.offline])), 
                str(emojis.offline) +' '+ _("Bots Offline"): mlcode(len([m for m in members if m.bot and m.status == Status.offline])), 
            }
        for name, value in infos.items():
            embed.add_field(name=name, value=value)
        return embed

translator = {
    'unknown': _("unknown"),
    'playing': _("playing"),
    'streaming': _("streaming"),
    'listening': _("listening"),
    'watching': _("watching"),
    'custom': _("custom"),
    'competing': _("competing in")
}

class ActivitiesSource(ListPageSource):
    guild: Guild
    def __init__(self, ctx: Union[ShakeContext, Interaction], guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        self.counter = {
            k: v 
            for k, v in Counter(set(
                    (member.activities[0].type, member.activities[0].name) for member in guild.members if not member.bot and bool(member.activities) and not member.activities[0].name is None
            )).most_common() if not (k[0].value == 4 and v == 1)
        }
        super().__init__(ctx, items=list(self.counter.keys()), title=MISSING, label=_("Activities"), paginating=True, per_page=10, *args, **kwargs)

    def format_page(self, menu: Menu, items: Tuple[ActivityType, str],  **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Activities"))
        prefix = str(PartialEmoji(name='dot', id=1093146860182568961)) + ''
        for type, name in items:
            index = self.counter[(type, name)]
            i = self.items.index((type, name)) + 1
            _type = translator.get(str(type.name), str(type.name))
            
            to_long = len(str(name)) > 31

            _name = name[0:28]+'[...]' if to_long else name
            _name = f'„{_name}“'.lower() if type.value == 4 else _name

            embed.add_field(
                name=prefix + _("Top {index} Activity ({type})").format(_='`',index='`'+str(i)+'`', type=_type),
                value='**({}):** '.format(index) + _name
            )
            if (items.index((type, name)) + 1)%2==0:
                embed.add_field(name=f'\u200b', value='\u200b', inline=True)
        embed.set_footer(text=_('Page {page} of {pages}').format(page=menu.page + 1, pages=self.maximum))
        return embed


features = Union[RolesSource, AssetsSource, EmojisSource, ChannelsSource, MembersSource, ActivitiesSource, PremiumSource]


class ServerItems(AnyPageSource):
    def __init__(self, ctx: ShakeContext, group: features, **kwargs) -> None:
        super().__init__()
        self.ctx = ctx
        self.group: features = group

    def is_paginating(self) -> bool: 
        return True
    
    def get_max_pages(self) -> Optional[int]:
        return self.group.get_max_pages()

    async def get_page(self, page: int) -> Any:
        source = await self.group.get_page(page)
        return source

    def format_page(self, *args: Any, **kwargs: Any) -> Tuple[ShakeEmbed, File]:
        embed = self.group.format_page(*args, **kwargs)
        return embed, None


class Front(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        guild = menu.guild
        embed = ShakeEmbed.default(menu.ctx, title=_("General Overview"), description='„'+guild.description+'“' if guild.description else None)
        recovery = 'https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png'
        embed.set_thumbnail(url=getattr(menu.guild.icon, 'url', recovery))


        embed.add_field(name=_("Created"), value=str(format_dt(guild.created_at, style="F")))
        region = Counter((channel.rtc_region if not channel.rtc_region is None else 'en-US'  for channel in guild.voice_channels+guild.stage_channels)).most_common(1)
        result = region[0][0] if bool(region) else 'en-US'
        embed.add_field(name=_("Region"), value=str(result))

        embed.add_field(name='\u200b', value='\u200b')

        bots = len([member for member in guild.members if member.bot])
        status = Counter(str(member.status) for member in guild.members)
        emojis = menu.bot.emojis.status
        statuses = '︱'.join([
            str(emojis.online) + code(status['online']), str(emojis.idle) + code(status['idle']),
            str(emojis.dnd) + code(status['dnd']), str(emojis.offline) + code(status['offline'])
        ])
        embed.add_field(
            name=_("Members"), 
            value=f'__**{len(set(m for m in guild.members if not m.bot))}**__ (+{bots} {_("Bots")})\n{statuses}', inline=False
            )

        more: Dict[str, str] = {
            _("ID"): f'`{guild.id}`',
            _("Owner"): f'{guild.owner.mention}',
            _("Roles"): f'`{len(guild.roles)}`',
            _("Emojis"): f'`{len(guild.emojis)}/{guild.emoji_limit}`',
            _("Stickers"): f'`{len(guild.stickers)}/{guild.sticker_limit}`',
            _("Boost"): f'`{_("{count} Boosts (Level {tier})").format(count=guild.premium_subscription_count, tier=guild.premium_tier)}`',
        }


        embed.add_field(name=_("More Information"), value='\n'.join(f'**{k}:** **{v}**' for k, v in more.items()), inline=False)
        embed.set_image(url=getattr(guild.banner, 'url', None))


        return embed, None