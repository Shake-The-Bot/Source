from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union, get_args

from discord import (
    CategoryChannel,
    File,
    ForumChannel,
    Guild,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
)
from discord.abc import GuildChannel
from discord.activity import ActivityType
from discord.enums import Status
from discord.ext import menus
from discord.utils import format_dt

from Classes import ShakeBot, ShakeCommand, ShakeContext, ShakeEmbed, _
from Classes.accessoires import (
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
    SourceSource,
    page,
)
from Classes.types import TextFormat, Translated, Types
from Classes.useful import MISSING, human_join

TYPES = Union[
    CategoryChannel, ForumChannel, StageChannel, TextChannel, Thread, VoiceChannel
]


############
#

# mention, id, type, name, category, bitrate/1000, position+1, user_limit, created_at


class command(ShakeCommand):
    def __init__(self, ctx, channel: GuildChannel):
        super().__init__(ctx)
        self.channel: TYPES = channel

    async def __await__(self):
        categories = dict()
        if isinstance(self.channel, CategoryChannel):
            front = CategoryFront()
            if bool(self.channel.text_channels):
                categories[TextChannelsSource(ctx=self.ctx, category=self.channel)] = 1
            if bool(self.channel.voice_channels + self.channel.stage_channels):
                categories[VoiceChannelsSource(ctx=self.ctx, category=self.channel)] = 1
        elif isinstance(self.channel, TextChannel):
            front = TextChannelFront()
        else:
            front = Front()

        select = CategoricalSelect(self.ctx, source=SourceSource)
        menu = Menu(ctx=self.ctx, source=front, channel=self.channel, select=select)
        menu.add_categories(categories=categories)

        if await menu.setup():
            await menu.send(ephemeral=True)


class Menu(CategoricalMenu):
    def __init__(
        self,
        ctx: ShakeContext,
        source: menus.PageSource,
        channel: GuildChannel,
        select: Optional[CategoricalSelect] = None,
        front: Optional[FrontPageSource] = None,
    ):
        self.channel: GuildChannel = channel
        super().__init__(ctx, source=source, select=select, front=front)

    def embed(self, embed: ShakeEmbed):
        embed.set_author(name=self.channel.name)
        return embed


""" Category """


class CategoryFront(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        ctx = menu.ctx
        category: CategoryChannel = menu.channel
        embed = ShakeEmbed.default(
            ctx,
            title=_("General Overview"),
        )
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(category.guild.icon, "url", recovery))

        embed.add_field(
            name=_("Created"),
            value=TextFormat.multiblockquotes(
                TextFormat.join(
                    format_dt(category.created_at, "F"),
                    "(" + format_dt(category.created_at, "R") + ")",
                )
            ),
            inline=False,
        )

        region = Counter(
            filter(
                lambda r: r is not None,
                [
                    getattr(channel, "rtc_region", None)
                    for channel in category.voice_channels + category.stage_channels
                ],
            )
        ).most_common(1)
        result = region[0][0] if bool(region) else _("No region supporting channels")
        embed.add_field(name=_("Region"), value=TextFormat.blockquotes(result))

        more: Dict[str, str] = {
            _("ID"): f"`{category.id}`",
        }

        embed.add_field(
            name=_("More Information"),
            value=TextFormat.multiblockquotes(
                "\n".join(f"**{k}:** **{v}**" for k, v in more.items())
            ),
            inline=False,
        )
        return embed, None


class TextChannelsSource(ListPageSource):
    category: CategoryChannel
    channels: List[ForumChannel, StageChannel, TextChannel, VoiceChannel]

    def __init__(self, ctx: ShakeContext, category: CategoryChannel, *args, **kwargs):
        self.category = category
        self.channels = category.text_channels
        super().__init__(
            ctx,
            items=self.channels,
            title=MISSING,
            label=_("Channels"),
            paginating=True,
            per_page=1,
            *args,
            **kwargs,
        )

    def format_page(
        self,
        menu: Menu,
        items: List[TextChannel],
        **kwargs: Any,
    ) -> ShakeEmbed:
        embed, File = TextChannelFront().channel(menu=menu, channel=items)
        embed.title = str(items.name)
        embed.set_footer(
            text=_("Page {page}/{pages} (Total of {items} Channels)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.items)
            )
        )
        return embed, File


class VoiceChannelsSource(ListPageSource):
    category: CategoryChannel
    channels: List[ForumChannel, StageChannel, TextChannel, VoiceChannel]

    def __init__(self, ctx: ShakeContext, category: CategoryChannel, *args, **kwargs):
        self.category = category
        self.channels = category.voice_channels + category.stage_channels
        super().__init__(
            ctx,
            items=self.channels,
            title=MISSING,
            label=_("Channels"),
            paginating=True,
            per_page=6,
            *args,
            **kwargs,
        )

    def format_page(
        self,
        menu: Menu,
        items: List[ForumChannel, StageChannel, TextChannel, VoiceChannel],
        **kwargs: Any,
    ) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Category channels"))
        for channel in items:
            embed.add_field(name=channel.name, value=channel.id, inline=False)
        embed.set_footer(
            text=_("Page {page}/{pages} (Total of {items} Channels)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.items)
            )
        )
        return embed, None


""" TextChannel """


class TextChannelFront(FrontPageSource):
    def format_page(self, menu: page.menus, page: Any) -> Tuple[ShakeEmbed, File]:
        return self.channel(menu, menu.channel)

    def channel(self, menu: Menu, channel: TextChannel):
        # TODO: slowmode info
        ctx = menu.ctx

        embed = ShakeEmbed.default(
            ctx,
            title=_("General Overview"),
            description="„" + channel.topic + "“" if channel.topic else None,
        )
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(channel.guild.icon, "url", recovery))

        embed.add_field(
            name=_("Created"),
            value=TextFormat.multiblockquotes(
                TextFormat.join(
                    format_dt(channel.created_at, "F"),
                    "(" + format_dt(channel.created_at, "R") + ")",
                    splitter="\n",
                )
            ),
        )

        embed.add_field(
            name=_("NSFW"),
            value=TextFormat.blockquotes(
                (menu.bot.emojis.no, menu.bot.emojis.yes)[channel.nsfw]
            ),
        )

        embed.add_field(
            name=_("Channel's server"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(channel.guild.name)
            ),
            inline=False,
        )

        embed.add_field(
            name=_("Channel's category"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(channel.category.name)
            ),
        )

        embed.add_field(
            name=_("Channel's position"),
            value=TextFormat.multiblockquotes(
                TextFormat.multicodeblock(
                    "#"
                    + str(channel.position)
                    + " / "
                    + str(len(channel.guild.channels)),
                    "css",
                )
            ),
        )

        more: Dict[str, str] = {
            _("ID"): f"`{channel.id}`",
        }

        embed.add_field(
            name=_("More Information"),
            value=TextFormat.multiblockquotes(
                "\n".join(f"**{k}:** **{v}**" for k, v in more.items())
            ),
            inline=False,
        )
        return embed, None


""" Front """


class Front(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        return self.guild(menu.ctx, menu.guild), None

    def guild(self, ctx: ShakeContext, guild: Guild):
        embed = ShakeEmbed.default(
            ctx,
            title=_("General Overview"),
            description="„" + guild.description + "“" if guild.description else None,
        )
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(guild.icon, "url", recovery))

        embed.add_field(
            name=_("Created"),
            value=TextFormat.blockquotes(format_dt(guild.created_at, style="F")),
        )
        region = Counter(
            filter(
                lambda r: r is not None,
                [
                    getattr(channel, "rtc_region", None)
                    for channel in guild.voice_channels + guild.stage_channels
                ],
            )
        ).most_common(1)
        result = region[0][0] if bool(region) else _("No region supporting channels")
        embed.add_field(name=_("Region"), value=TextFormat.blockquotes(result))

        bots = len([member for member in guild.members if member.bot])
        status = Counter(str(member.status) for member in guild.members)
        emojis = ctx.bot.emojis.status
        statuses = "︱".join(
            [
                str(emojis.online) + TextFormat.codeblock(status["online"]),
                str(emojis.idle) + TextFormat.codeblock(status["idle"]),
                str(emojis.dnd) + TextFormat.codeblock(status["dnd"]),
                str(emojis.offline) + TextFormat.codeblock(status["offline"]),
            ]
        )
        members = TextFormat.underline(
            TextFormat.bold(len(set(m for m in guild.members if not m.bot)))
        )
        embed.add_field(
            name=_("Members"),
            value=TextFormat.multiblockquotes(
                f'{members} (+{bots} {_("Bots")})\n{statuses}'
            ),
            inline=False,
        )

        more: Dict[str, str] = {
            _("ID"): f"`{guild.id}`",
            _("Owner"): f"{guild.owner.mention}",
            _("Roles"): f"`{len(guild.roles)}`",
            _("Emojis"): f"`{len(guild.emojis)}/{guild.emoji_limit}`",
            _("Stickers"): f"`{len(guild.stickers)}/{guild.sticker_limit}`",
            _(
                "Boost"
            ): f'`{_("{count} Boosts (Level {tier})").format(count=guild.premium_subscription_count, tier=guild.premium_tier)}`',
        }

        embed.add_field(
            name=_("More Information"),
            value=TextFormat.multiblockquotes(
                "\n".join(f"**{k}:** **{v}**" for k, v in more.items())
            ),
            inline=False,
        )
        embed.set_image(url=getattr(guild.banner, "url", None))

        return embed


category = CategoryFront | TextChannelsSource | VoiceChannelsSource
text = TextChannelFront
