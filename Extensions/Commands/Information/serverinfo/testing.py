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

from Classes import ShakeBot, ShakeCommand, ShakeContext, ShakeEmbed, _
from Classes.accessoires import (
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
    SourceSource,
)
from Classes.types import Format, Translated, Types
from Classes.useful import MISSING, human_join

############
#


class command(ShakeCommand):
    def __init__(self, ctx, guild: Guild):
        super().__init__(ctx)
        self.guild: Guild = guild

    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=SourceSource)
        menu = Menu(ctx=self.ctx, source=Front(), guild=self.guild, select=select)

        categoies = {
            RolesSource(ctx=self.ctx, guild=self.guild): set(self.guild.roles),
            ChannelsSource(ctx=self.ctx, guild=self.guild): set(self.guild.channels),
            MembersSource(ctx=self.ctx, guild=self.guild): set(self.guild.members),
            BadgesSource(ctx=self.ctx, guild=self.guild): 1,
            PremiumSource(ctx=self.ctx, guild=self.guild): set(
                self.guild.premium_subscribers
            ),
        }
        for member in self.guild.members:
            if filter(lambda a: a.type != ActivityType.custom, member.activities):
                categoies[ActivitiesSource(ctx=self.ctx, guild=self.guild)] = 1
                break

        if bool(self.guild.emojis):
            categoies[EmojisSource(ctx=self.ctx, guild=self.guild)] = [
                self.guild.icon,
                self.guild.banner,
                self.guild.splash,
                self.guild.discovery_splash,
            ]

        assets: Dict[Asset, str] = {
            self.guild.icon: _("Servers's icon"),
            self.guild.splash: _("Servers's splash"),
            self.guild.discovery_splash: _("Server's discovery splash"),
            self.guild.banner: _("Servers's banner"),
        }
        if any(bool(_) for _ in assets):
            categoies[assetsource(ctx=self.ctx, guild=self.guild, items=assets)] = set(
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
                "ID:": f"{Format.codeblock(role.id)}",
                _("Created") + ":": str(format_dt(role.created_at, "f")),
                _("Mention") + ":": role.mention if member else "@" + role.name,
                _("Colour") + ":": Format.codeblock(str(role.colour))
                if not role.colour == Colour.default()
                else _("Default"),
            }
            text = "\n".join(
                f"{Format.bold(key)} {value}" for key, value in infos.items()
            )
            embed.add_field(name=f"` {i}. ` " + name, value=text, inline=True)
            if ii % 2 == 0:
                embed.add_field(name=f"\u200b", value="\u200b", inline=True)
        embed.set_footer(
            text=_("Page {page}/{pages} (Total of {items} Roles)").format(
                page=menu.page + 1, pages=self.maximum, items=len(self.items)
            )
        )
        return embed, None


class assetsource(ListPageSource):
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
                Format.hyperlink(
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
                "ID:": f"{Format.codeblock(emoji.id)}",
                _("Created") + ":": str(format_dt(emoji.created_at, "f")),
                _("Twitch") + "?": _("Yes") if emoji.managed else _("No"),
                _("Added") + ":": emoji.user.mention
                if emoji.user in self.guild.members
                else emoji.user,
            }
            text = "\n".join(
                f"{Format.bold(key)} {value}"
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
            categories=Format.bold(categories),
            voices=Format.bold(voices),
            stages=Format.bold(stages),
            forums=Format.bold(forums),
            texts=Format.bold(texts),
            threads=Format.bold(threads),
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
        emojis = self.bot.assets.status
        member = PartialEmoji(name="\N{BUSTS IN SILHOUETTE}")
        human = PartialEmoji(name="\N{BUST IN SILHOUETTE}")
        bot = PartialEmoji(name="\N{ROBOT FACE}")
        infos = {
            str(member) + " " + _("Total Members"): Format.multicodeblock(len(members)),
            str(human)
            + " "
            + _("Total Humans"): Format.multicodeblock(
                len([m for m in members if not m.bot])
            ),
            str(bot)
            + " "
            + _("Total Bots"): Format.multicodeblock(
                len([m for m in members if m.bot])
            ),
            str(emojis.online)
            + " "
            + _("Total Online"): Format.multicodeblock(
                len([m for m in members if m.status == Status.online])
            ),
            str(emojis.online)
            + " "
            + _("Humans Online"): Format.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.online])
            ),
            str(emojis.online)
            + " "
            + _("Bots Online"): Format.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.online])
            ),
            str(emojis.idle)
            + " "
            + _("Total Idle"): Format.multicodeblock(
                len([m for m in members if m.status == Status.idle])
            ),
            str(emojis.idle)
            + " "
            + _("Humans Idle"): Format.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.idle])
            ),
            str(emojis.idle)
            + " "
            + _("Bots Idle"): Format.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.idle])
            ),
            str(emojis.dnd)
            + " "
            + _("Total DND"): Format.multicodeblock(
                len([m for m in members if m.status == Status.dnd])
            ),
            str(emojis.dnd)
            + " "
            + _("Humans DND"): Format.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.dnd])
            ),
            str(emojis.dnd)
            + " "
            + _("Bots DND"): Format.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.dnd])
            ),
            str(emojis.offline)
            + " "
            + _("Total Offline"): Format.multicodeblock(
                len([m for m in members if m.status == Status.offline])
            ),
            str(emojis.offline)
            + " "
            + _("Humans Offline"): Format.multicodeblock(
                len([m for m in members if not m.bot and m.status == Status.offline])
            ),
            str(emojis.offline)
            + " "
            + _("Bots Offline"): Format.multicodeblock(
                len([m for m in members if m.bot and m.status == Status.offline])
            ),
        }
        for name, value in infos.items():
            embed.add_field(name=name, value=value)
        return embed, None


class BadgesSource(ItemPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        members = guild.members
        self.all = list(dict(members[0].public_flags).keys())

        flags = Counter(
            flag
            for member in members
            for flag, has in dict(member.public_flags).items()
            if has
        )
        bots = Counter("bot" for member in members if member.bot)

        counted = flags | bots

        super().__init__(
            ctx,
            item=counted,
            title=MISSING,
            label=_("Badges"),
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Server Member Badges"))

        badges = [
            (
                emoji,
                " ".join(
                    list(_.capitalize() for _ in str(badge).replace("_", " ").split())
                ),
                Format.bold(self.item.get(badge, 0)),
            )
            for badge in self.all
            if (emoji := self.bot.get_emoji_local("badges", badge))
        ]

        embed.description = "\n".join(
            list(
                "{} {}: {}".format(emoji, name, count) for emoji, name, count in badges
            )
        )

        return embed, None


class ActivitiesSource(ListPageSource):
    guild: Guild

    def __init__(self, ctx: ShakeContext | Interaction, guild: Guild, *args, **kwargs):
        self.guild: Guild = guild
        activities = [
            (activity.type, activity.name)
            for activity in [
                member.activities[0]
                for member in guild.members
                if bool(member.activities)
            ]
            if not activity.name is None and activity.type.value != 4
        ]
        counter = Counter(activities).most_common()
        self.counter = {(t, n): v for (t, n), v in counter if v > 1}
        self.places = list(sorted(set(self.counter.values()), reverse=True))
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
            people = self.counter[(type, name)]
            i = self.places.index(people) + 1
            _type = str(type.name)

            to_long = len(str(name)) > 31

            _name = name[0:28] + "[...]" if to_long else name
            _name = f"„{_name}“".lower() if type.value == 4 else _name

            embed.add_field(
                name=prefix
                + _("Top {index} Activity ({type})").format(
                    _="`", index="`" + str(i) + "`", type=_type
                ),
                value="({}): ".format(Format.bold(people)) + _name,
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
    | assetsource
    | EmojisSource
    | ChannelsSource
    | MembersSource
    | ActivitiesSource
    | PremiumSource
)


class Front(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        return self.guild(menu.ctx, menu.guild), None

    def guild(self, ctx: ShakeContext, guild: Guild):
        embed = ShakeEmbed.default(
            ctx,
            title=_("General Overview"),
            description=Format.multicodeblock("„" + guild.description + "“")
            if guild.description
            else None,
        )
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(guild.icon, "url", recovery))

        embed.add_field(
            name=_("Created"),
            value=Format.multiblockquotes(
                Format.join(
                    format_dt(guild.created_at, "F"),
                    "(" + format_dt(guild.created_at, "R") + ")",
                )
            ),
            inline=False,
        )

        bots = len([member for member in guild.members if member.bot])
        status = Counter(str(member.status) for member in guild.members)
        emojis = ctx.bot.assets.status
        statuses = "︱".join(
            [
                str(emojis.online) + Format.codeblock(status["online"]),
                str(emojis.idle) + Format.codeblock(status["idle"]),
                str(emojis.dnd) + Format.codeblock(status["dnd"]),
                str(emojis.offline) + Format.codeblock(status["offline"]),
            ]
        )
        members = Format.underline(
            Format.bold(len(set(m for m in guild.members if not m.bot)))
        )
        embed.add_field(
            name=_("Members"),
            value=Format.multiblockquotes(
                f'{members} (+{bots} {_("Bots")})\n{statuses}'
            ),
            inline=False,
        )

        if guild.me:
            embed.add_field(
                name=_("Servers's position"),
                value=Format.blockquotes(
                    Format.bold(
                        "#"
                        + str(
                            sum(
                                g.me.joined_at < guild.me.joined_at
                                for g in ctx.bot.guilds
                            )
                            + 1
                        )
                        + " / "
                        + str(len(ctx.bot.guilds))
                    )
                ),
            )

        region = Counter(
            (
                channel.rtc_region if not channel.rtc_region is None else "en-US"
                for channel in guild.voice_channels + guild.stage_channels
            )
        ).most_common(1)
        result = region[0][0] if bool(region) else "en-US"
        embed.add_field(name=_("Region"), value=Format.blockquotes(Format.bold(result)))

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
            value=Format.multiblockquotes(
                "\n".join(
                    [
                        Format.join(Format.bold(k), Format.bold(v), splitter=": ")
                        for k, v in more.items()
                    ]
                )
            ),
            inline=False,
        )
        embed.set_image(url=getattr(guild.banner, "url", None))

        embed.advertise(ctx.bot)
        return embed
