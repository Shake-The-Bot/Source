from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, get_args

from discord import (
    Asset,
    CategoryChannel,
    Colour,
    Emoji,
    File,
    Guild,
    Interaction,
    Member,
    PartialEmoji,
    Role,
)
from discord.activity import ActivityType
from discord.enums import Status
from discord.ext import menus
from discord.utils import format_dt

from Classes import ShakeCommand, ShakeContext, ShakeEmbed, _
from Classes.accessoires import (
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
    SourceSource,
)
from Classes.types import TextFormat, Types, tick
from Classes.useful import MISSING, human_join

############
#


class command(ShakeCommand):
    def __init__(self, ctx, guild: Guild):
        super().__init__(ctx)
        self.guild: Guild = guild

    def channelinfo(
        self,
    ) -> Dict[str, str]:
        information = dict()
        emojis = (self.bot.emojis.hook, self.bot.emojis.cross)
        information[_("Categories") + ":"] = (
            "`" + str((len(self.guild.categories))) + "`"
        )
        information[_("Text Channels") + ":"] = (
            "`"
            + str(
                len(
                    [channel for channel in self.guild.text_channels if channel.is_news]
                )
            )
            + "`"
        )
        information[_("Voice Channels") + ":"] = (
            "`" + str(len(self.guild.voice_channels)) + "`"
        )
        information[_("Stages") + ":"] = "`" + str(len(self.guild.stage_channels)) + "`"
        information[_("Forums") + ":"] = "`" + str(len(self.guild.forums)) + "`"
        information[_("Threads") + ":"] = "`" + str(len(self.guild.threads)) + "`"
        information[_("Rules Channel") + ":"] = emojis[bool(self.guild.rules_channel)]
        information[_("Announcements") + ":"] = (
            "`"
            + str(
                len(
                    [
                        channel
                        for channel in self.guild.text_channels
                        if not channel.is_news
                    ]
                )
            )
            + "`"
        )
        return information

    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=SourceSource)
        menu = Menu(ctx=self.ctx, source=Front(), guild=self.guild, select=select)

        categoies = {
            RolesSource(ctx=self.ctx, guild=self.guild): set(self.guild.roles),
            EmojisSource(ctx=self.ctx, guild=self.guild): [
                self.guild.icon,
                self.guild.banner,
                self.guild.splash,
                self.guild.discovery_splash,
            ],
            ChannelsSource(ctx=self.ctx, guild=self.guild): set(self.guild.channels),
            MembersSource(ctx=self.ctx, guild=self.guild): set(self.guild.members),
            ActivitiesSource(ctx=self.ctx, guild=self.guild): set(
                m.activities for m in self.guild.members
            ),
            PremiumSource(ctx=self.ctx, guild=self.guild): set(
                self.guild.premium_subscribers
            ),
        }
        assets: Dict[Asset, str] = {
            self.guild.icon: _("Servers's icon"),
            self.guild.splash: _("Servers's splash"),
            self.guild.discovery_splash: _("Server's discovery splash"),
            self.guild.banner: _("Servers's banner"),
        }
        if any(bool(_) for _ in assets):
            categoies[AssetsSource(ctx=self.ctx, guild=self.guild, items=assets)] = set(
                assets
            )

        menu.add_categories(categories=categoies)
        if await menu.setup():
            await menu.send(ephemeral=True)


class Menu(CategoricalMenu):
    def __init__(
        self,
        ctx: ShakeContext,
        source: menus.PageSource,
        guild: Guild,
        select: Optional[CategoricalSelect] = None,
        front: Optional[FrontPageSource] = None,
    ):
        self.guild: Guild = guild
        super().__init__(ctx, source=source, select=select, front=front)

    def embed(self, embed: ShakeEmbed):
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_author(
            name=self.guild.name, icon_url=getattr(self.guild.icon, "url", recovery)
        )
        return embed


class RolesSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        roles: List[Role] = sorted(
            [role for role in guild.roles if not role == guild.default_role],
            reverse=True,
        )
        super().__init__(
            ctx,
            items=roles,
            title=MISSING,
            label=_("Roles"),
            paginating=True,
            per_page=6,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: List[Role], **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Roles"))
        for role in items:
            i = self.items.index(role) + 1
            ii = items.index(role) + 1
            to_long = len(role.name) > 20
            name = "@" + (role.name[0:15] + "[...]" if to_long else role.name)
            member = menu.ctx.author in self.guild.members
            infos = {
                "ID:": f"{TextFormat.codeblock(role.id)}",
                _("Created") + ":": str(format_dt(role.created_at, "f")),
                _("Mention") + ":": role.mention if member else "@" + role.name,
                _("Colour") + ":": TextFormat.codeblock(str(role.colour))
                if not role.colour == Colour.default()
                else _("Default"),
            }
            text = "\n".join(f"**{key}** {value}" for key, value in infos.items())
            embed.add_field(name=f"` {i}. ` " + name, value=text, inline=True)
            if ii % 2 == 0:
                embed.add_field(name=f"\u200b", value="\u200b", inline=True)
        embed.set_footer(
            text=_("Page {page}/{pages} (Total of {items} Roles)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.items)
            )
        )
        return embed, None


class AssetsSource(ListPageSource):
    guild: Guild

    def __init__(
        self,
        ctx: ShakeContext,
        items: Dict[Optional[Asset], str],
        guild: Guild,
        *args,
        **kwargs,
    ):
        self.guild: Guild = guild
        self.from_dict = items

        super().__init__(
            ctx,
            items=list(x for x in items if x),
            title=MISSING,
            label=_("Avatar/Banner"),
            paginating=True,
            per_page=1,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: Asset, **kwargs: Any) -> ShakeEmbed:
        listed = []
        formattypes = list(
            get_args(
                Types.ValidAssetFormatTypes.value
                if items.is_animated()
                else Types.ValidStaticFormatTypes.value
            )
        )
        for formattype in formattypes:
            listed.append(
                TextFormat.hyperlink(
                    str(formattype).upper(),
                    items.replace(size=1024, format=f"{formattype}").url,
                )
            )
        avatars = _("Open link: {links}").format(links=", ".join(listed))
        embed = ShakeEmbed(
            title=self.from_dict[items], description=avatars if bool(avatars) else None
        )
        embed.set_image(url=items.url)
        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed, None


class EmojisSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        emojis: List[Emoji] = sorted(
            guild.emojis, key=lambda e: e.animated, reverse=True
        )
        super().__init__(
            ctx,
            items=emojis,
            title=MISSING,
            label=_("Emojis"),
            paginating=True,
            per_page=8,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: List[Emoji], **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Emojis"))
        for emoji in items:
            i = self.items.index(emoji) + 1
            ii = items.index(emoji) + 1
            infos = {
                "ID:": f"{TextFormat.codeblock(emoji.id)}",
                _("Created") + ":": str(format_dt(emoji.created_at, "f")),
                _("Twitch") + "?": _("Yes") if emoji.managed else _("No"),
                _("Added") + ":": emoji.user.mention
                if emoji.user in self.guild.members
                else emoji.user,
            }
            text = "\n".join(
                f"**{key}** {value}"
                for key, value in infos.items()
                if all([key is not None, value is not None])
            )
            embed.add_field(name=str(emoji), value=text)
            if ii % 2 == 0:
                embed.add_field(name=f"\u200b", value="\u200b", inline=True)
        embed.set_footer(
            text=_("Page {page} of {pages} (Total of {items} Emojis)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.items)
            )
        )
        return embed, None


class PremiumSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        subscriber: List[Member] = set(guild.premium_subscribers)
        super().__init__(
            ctx,
            items=subscriber,
            title=MISSING,
            label=_("Nitro Booster"),
            paginating=True,
            per_page=25,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: List[Member], **kwargs: Any) -> ShakeEmbed:
        description = (
            ", ".join(
                [
                    m.mention if self.ctx.author in self.guild.members else str(m)
                    for m in items
                ]
            )
            or ""
        )
        embed = ShakeEmbed(title=_("Server Nitro Booster"), description=description)

        embed.set_footer(
            text=_("Page {page} of {pages} (Total of {items} Booster)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.entries)
            )
        )
        return embed, None


class ChannelsSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        channels: List[Types.GuildChannel.value] = sorted(
            filter(
                lambda channel: not isinstance(channel, CategoryChannel),
                [channel for channel in guild.channels],
            ),
            key=lambda channel: channel.position,
        )
        self.categories = sorted(
            set(channel.category for channel in channels),
            key=lambda category: getattr(category, "position", -1),
        )
        super().__init__(
            ctx,
            items=channels,
            title=MISSING,
            label=_("Channels"),
            paginating=True,
            per_page=25,
            *args,
            **kwargs,
        )

    def format_page(
        self, menu: Menu, items: List[Types.GuildChannel.value], **kwargs: Any
    ) -> ShakeEmbed:
        categories, voices, stages, texts, forums, threads = (
            len(self.guild.categories),
            len(self.guild.stage_channels),
            len(self.guild.stage_channels),
            len(self.guild.text_channels),
            len(self.guild.forums),
            len(self.guild.threads),
        )

        description = _(
            "{categories} Categorie-, {voices} Voice-, {stages} Stage-, {forums} Forum- and {texts} Textchannel with {threads} Threads"
        ).format(
            categories=TextFormat.bold(categories),
            voices=TextFormat.bold(voices),
            stages=TextFormat.bold(stages),
            forums=TextFormat.bold(forums),
            texts=TextFormat.bold(texts),
            threads=TextFormat.bold(threads),
        )
        embed = ShakeEmbed(title=_("Server Channels"), description=description)

        categories = sorted(
            set(channel.category for channel in items),
            key=lambda category: getattr(category, "position", -1),
        )
        summedup = {
            category: [channel for channel in items if channel.category == category]
            for category in categories
        }

        for category in summedup.keys():
            i = self.categories.index(category) + 1
            channels = sorted(summedup[category], key=lambda channel: channel.position)
            value = human_join(list(channel.mention for channel in channels))
            if not menu.ctx.author in self.guild.members:
                value = human_join(list("#" + channel.name for channel in channels))
            embed.add_field(
                name=f"` {i}. ` " + "#" + (category.name if category else _("NO CAT")),
                value=value,
                inline=False,
            )

        embed.set_footer(
            text=_("Page {page} of {pages} (Total of {items} Channels)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.entries)
            )
        )
        return embed, None


class MembersSource(ItemPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        super().__init__(
            ctx,
            item=guild.members,
            title=MISSING,
            label=_("Members"),
            paginating=True,
            per_page=25,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        members: List[Member] = self.item
        embed = ShakeEmbed(title=_("Server Members"))
        emojis = self.bot.emojis.status
        member = PartialEmoji(name="\N{BUSTS IN SILHOUETTE}")
        human = PartialEmoji(name="\N{BUST IN SILHOUETTE}")
        bot = PartialEmoji(name="\N{ROBOT FACE}")
        infos = {
            str(member)
            + " "
            + _("Total Members"): TextFormat.multicodeblock(len(members)),
            str(human)
            + " "
            + _("Total Humans"): TextFormat.multicodeblock(
                len([m for m in members if not m.bot])
            ),
            str(bot)
            + " "
            + _("Total Bots"): TextFormat.multicodeblock(
                len([m for m in members if m.bot])
            ),
            str(emojis.online)
            + " "
            + _("Total Online"): TextFormat.multicodeblock(
                len([m for m in members if m.status == Status.online])
            ),
            str(emojis.online)
            + " "
            + _("Humans Online"): TextFormat.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.online])
            ),
            str(emojis.online)
            + " "
            + _("Bots Online"): TextFormat.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.online])
            ),
            str(emojis.idle)
            + " "
            + _("Total Idle"): TextFormat.multicodeblock(
                len([m for m in members if m.status == Status.idle])
            ),
            str(emojis.idle)
            + " "
            + _("Humans Idle"): TextFormat.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.idle])
            ),
            str(emojis.idle)
            + " "
            + _("Bots Idle"): TextFormat.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.idle])
            ),
            str(emojis.dnd)
            + " "
            + _("Total DND"): TextFormat.multicodeblock(
                len([m for m in members if m.status == Status.dnd])
            ),
            str(emojis.dnd)
            + " "
            + _("Humans DND"): TextFormat.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.dnd])
            ),
            str(emojis.dnd)
            + " "
            + _("Bots DND"): TextFormat.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.dnd])
            ),
            str(emojis.offline)
            + " "
            + _("Total Offline"): TextFormat.multicodeblock(
                len([m for m in members if m.status == Status.offline])
            ),
            str(emojis.offline)
            + " "
            + _("Humans Offline"): TextFormat.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.offline])
            ),
            str(emojis.offline)
            + " "
            + _("Bots Offline"): TextFormat.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.offline])
            ),
        }
        for name, value in infos.items():
            embed.add_field(name=name, value=value)
        return embed, None


translator = {
    "unknown": _("unknown"),
    "playing": _("playing"),
    "streaming": _("streaming"),
    "listening": _("listening"),
    "watching": _("watching"),
    "custom": _("custom"),
    "competing": _("competing in"),
}


class ActivitiesSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        self.counter = {
            k: v
            for k, v in Counter(
                set(
                    (member.activities[0].type, member.activities[0].name)
                    for member in guild.members
                    if not member.bot
                    and bool(member.activities)
                    and not member.activities[0].name is None
                )
            ).most_common()
            if not (k[0].value == 4 and v == 1)
        }
        super().__init__(
            ctx,
            items=list(self.counter.keys()),
            title=MISSING,
            label=_("Activities"),
            paginating=True,
            per_page=10,
            *args,
            **kwargs,
        )

    def format_page(
        self, menu: Menu, items: Tuple[ActivityType, str], **kwargs: Any
    ) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Activities"))
        prefix = str(PartialEmoji(name="dot", id=1093146860182568961)) + ""
        for type, name in items:
            index = self.counter[(type, name)]
            i = self.items.index((type, name)) + 1
            _type = translator.get(str(type.name), str(type.name))

            to_long = len(str(name)) > 31

            _name = name[0:28] + "[...]" if to_long else name
            _name = f"„{_name}“".lower() if type.value == 4 else _name

            embed.add_field(
                name=prefix
                + _("Top {index} Activity ({type})").format(
                    _="`", index="`" + str(i) + "`", type=_type
                ),
                value="**({}):** ".format(index) + _name,
            )
            if (items.index((type, name)) + 1) % 2 == 0:
                embed.add_field(name=f"\u200b", value="\u200b", inline=True)
        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed, None


features = (
    RolesSource
    | AssetsSource
    | EmojisSource
    | ChannelsSource
    | MembersSource
    | ActivitiesSource
    | PremiumSource
)


class Front(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        guild = menu.guild
        embed = ShakeEmbed.default(
            menu.ctx,
            title=_("General Overview"),
            description="„" + guild.description + "“" if guild.description else None,
        )
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(menu.guild.icon, "url", recovery))

        embed.add_field(
            name=_("Created"),
            value=TextFormat.blockquotes(format_dt(guild.created_at, style="F")),
        )
        region = Counter(
            (
                channel.rtc_region if not channel.rtc_region is None else "en-US"
                for channel in guild.voice_channels + guild.stage_channels
            )
        ).most_common(1)
        result = region[0][0] if bool(region) else "en-US"
        embed.add_field(name=_("Region"), value=TextFormat.blockquotes(result))

        bots = len([member for member in guild.members if member.bot])
        status = Counter(str(member.status) for member in guild.members)
        emojis = menu.bot.emojis.status
        statuses = "︱".join(
            [
                str(emojis.online) + TextFormat.codeblock(status["online"]),
                str(emojis.idle) + TextFormat.codeblock(status["idle"]),
                str(emojis.dnd) + TextFormat.codeblock(status["dnd"]),
                str(emojis.offline) + TextFormat.codeblock(status["offline"]),
            ]
        )
        embed.add_field(
            name=_("Members"),
            value=TextFormat.multiblockquotes(
                f'__**{len(set(m for m in guild.members if not m.bot))}**__ (+{bots} {_("Bots")})\n{statuses}'
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

        return embed, None
