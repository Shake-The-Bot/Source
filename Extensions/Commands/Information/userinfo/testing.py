############
#
from inspect import cleandoc
from typing import Any, Dict, List, Optional, Tuple, get_args

from discord import (
    Asset,
    Colour,
    File,
    Guild,
    Interaction,
    Member,
    PartialEmoji,
    PublicUserFlags,
    Role,
    User,
)
from discord.activity import ActivityTypes
from discord.ext import menus
from discord.utils import format_dt

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _
from Classes.pages import (
    AnyPageSource,
    CategoricalMenu,
    CategoricalSelect,
    FrontPageSource,
    ItemPageSource,
    ListPageSource,
)
from Classes.types import TextFormat, Types
from Classes.useful import MISSING

########
#
tick = (
    "<:tickno1:1107414761148268626><:tickno2:1107414763010523166>",
    "<:tickyes1:1109463235909914694><:tickyes2:1109463231291990086>",
)
########
#


class command:
    def __init__(
        self,
        ctx: ShakeContext,
        user: User,
        member: Optional[Member] = None,
        fallback: Optional[Member] = None,
    ):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.user: User = user
        self.member: Optional[Member] = member
        self.fallback: Optional[Member] = fallback

    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=UserItems)
        menu = Menu(
            ctx=self.ctx,
            source=Front(),
            user=self.user,
            member=self.member,
            fallback=self.fallback,
            select=select,
        )

        categories = {
            BadgesSource(ctx=self.ctx, user=self.user): list(self.user.public_flags),
            AssetsSource(ctx=self.ctx, user=self.user): self.user.display_avatar,
            # AssetsSource(ctx=self.ctx, user=self.user): set(self.user.emojis),
            # EmojisSource(ctx=self.ctx, user=self.user): [self.user.icon, self.user.banner, self.user.splash, self.user.discovery_splash],
            # ChannelsSource(ctx=self.ctx, user=self.user): set(self.user.channels),
            # MembersSource(ctx=self.ctx, user=self.user): set(self.user.members),
            # ActivitiesSource(ctx=self.ctx, user=self.user): set(m.activities for m in self.user.members),
            # PremiumSource(ctx=self.ctx, user=self.user): set(self.user.premium_subscribers)
        }

        if self.member:
            member = {
                RolesSource(ctx=self.ctx, member=self.member): set(self.member.roles),
                PositionSource(ctx=self.ctx, member=self.member): list(
                    self.member.guild.members
                ),
            }
            categories = categories | member

        menu.add_categories(categories=categories)
        if await menu.setup():
            await menu.send()


class Menu(CategoricalMenu):
    def __init__(
        self,
        ctx: ShakeContext,
        source: menus.PageSource,
        user: User,
        member: Optional[Member] = None,
        fallback: Optional[Member] = None,
        select: Optional[CategoricalSelect] = None,
        front: Optional[FrontPageSource] = None,
    ):
        self.user: User = user
        self.member: Optional[Member] = member
        self.fallback: Optional[Member] = fallback
        super().__init__(ctx, source=source, select=select, front=front)

    def embed(self, embed: ShakeEmbed):
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_author(
            name=self.user.name, icon_url=getattr(self.user.avatar, "url", recovery)
        )
        return embed


class RolesSource(ListPageSource):
    guild: Guild

    def __init__(
        self, ctx: ShakeContext | Interaction, member: Member, *args, **kwargs
    ):
        self.member: Member = member
        self.guild: Guild = member.guild
        roles: List[Role] = sorted(
            [role for role in member.roles if not role == member.guild.default_role],
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
            is_member: bool = menu.ctx.author in self.guild.members
            infos = {
                "ID:": f"{TextFormat.codeblock(role.id)}",
                _("Created") + ":": str(format_dt(role.created_at, "f")),
                _("Mention") + ":": role.mention if is_member else "@" + role.name,
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
        return embed


class AssetsSource(ListPageSource):
    guild: Guild

    def __init__(
        self,
        ctx: ShakeContext | Interaction,
        user: User,
        member: Optional[Member] = None,
        *args,
        **kwargs,
    ):
        self.user: User = user
        self.member: Optional[Member] = member
        self.from_dict: Dict[Asset, str] = {
            member.avatar if member else user.avatar: _("User's Avatar"),
            member.display_avatar
            if member
            else getattr(user, "display_icon", None): _("User's Display Avatar"),
            member.guild_avatar if member else None: _("User's Guild Avatar"),
            user.banner: _("User's Banner"),
        }
        super().__init__(
            ctx,
            items=list(x for x in self.from_dict.keys() if x),
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
                Types.ValidAssetFormatTypes
                if items.is_animated()
                else Types.ValidStaticFormatTypes
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
        return embed


class PositionSource(ItemPageSource):
    guild: Guild

    def __init__(
        self, ctx: ShakeContext | Interaction, member: Member, *args, **kwargs
    ):
        self.member: Member = member
        self.guild: Guild = member.guild
        super().__init__(
            ctx,
            item=sorted(
                self.guild.members,
                key=lambda member: sum(
                    m.joined_at < member.joined_at for m in self.guild.members
                ),
            ),
            title=MISSING,
            label=_("Joining Postition"),
            paginating=True,
            per_page=25,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Joining Postition"))

        embed.add_field(
            name=_("Member's position").format(member=self.member.name),
            value=TextFormat.blockquotes(
                TextFormat.bold(
                    "#"
                    + str(
                        sum(
                            m.joined_at < self.member.joined_at
                            for m in self.guild.members
                        )
                        + 1
                    )
                    + " / "
                    + str(len(self.guild.members))
                )
            ),
        )
        embed.add_field(
            name=_("Joined on"),
            value=TextFormat.blockquotes(
                TextFormat.bold(format_dt(self.member.joined_at, style="F"))
            ),
        )

        index = self.item.index(self.member)

        lower = max(0, index - 6)
        upper = min(len(self.item) - 1, index + 6) + 1
        selected: List[Member] = self.item[lower:upper]

        embed.add_field(
            name="\u200b",
            value=TextFormat.multicodeblock(
                "\n".join(
                    [
                        (
                            "\n@ {pos}. {member}    ({date})\n"
                            if member == self.member
                            else "> {pos}. {member}    ({date})"
                        ).format(
                            member=str(member),
                            pos=sum(
                                m.joined_at < member.joined_at
                                for m in self.guild.members
                            )
                            + 1,
                            date=member.joined_at.strftime("%d-%m-%Y"),
                        )
                        for member in selected
                    ]
                ),
                "py",
            ),
            inline=False,
        )

        embed.set_footer(
            text=_("Total of {items} Members").format(items=len(self.guild.members))
        )
        return embed


class BadgesSource(ItemPageSource):
    user: User

    def __init__(self, ctx: ShakeContext | Interaction, user: User, *args, **kwargs):
        self.user: User = user
        super().__init__(
            ctx,
            item=user.public_flags,
            title=MISSING,
            label=_("Badges"),
            paginating=True,
            per_page=25,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        flags: set[PublicUserFlags] = set(self.item)
        embed = ShakeEmbed(title=_("User Badges"))
        is_animated = self.user.display_avatar.is_animated()

        if is_animated or self.user.banner:
            flags.add(("subscriber", True))

        for property in set([flag for flag, has in flags if has]):
            badge = self.ctx.bot.get_emoji_local("badges", property)
            name = " ".join(
                list(x.capitalize() for x in str(property).replace("_", " ").split())
            )
            embed.add_field(name=str(badge) + " " + name, value="\u200b")

        return embed


features = RolesSource | BadgesSource | AssetsSource | PositionSource


class UserItems(AnyPageSource):
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
        user: User = menu.user
        member: Optional[Member] = menu.member
        fallback: Optional[Member] = menu.fallback
        embed = ShakeEmbed.default(menu.ctx, title=_("General Overview"))
        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(user.avatar, "url", recovery))

        # embed.add_field(name=_("Joined Discord"), value=TextFormat.blockquotes(format_dt(user.created_at, style="F")))
        embed.add_field(name=_("Bot"), value=TextFormat.blockquotes(tick[user.bot]))
        embed.add_field(
            name=_("Discord System"), value=TextFormat.blockquotes(tick[user.system])
        )
        embed.add_field(
            name=_("Member"), value=TextFormat.blockquotes(tick[bool(member)])
        )

        if m := member or fallback:
            embed.description = (
                "„" + m.activities[0].name + "“"
                if bool(m.activities) and m.activities[0].type == m.status.value == 4
                else None
            )

            emojis = menu.bot.emojis.status
            emoji = {
                "online": str(emojis.online),
                "invisible": str(emojis.offline),
                "offline": str(emojis.offline),
                "idle": str(emojis.idle),
                "dnd": str(emojis.dnd),
            }.get(m.status.value)
            status = (
                {
                    "online": _("online"),
                    "offline": _("offline"),
                    "streaming": _("streaming"),
                    "idle": _("idle"),
                    "dnd": _("dnd"),
                }
                .get(m.status.value)
                .capitalize()
            )
            embed.add_field(
                name=_("Status"),
                value=TextFormat.blockquotes(TextFormat.bold(status)) + " " + emoji,
            )
            if member:
                embed.add_field(
                    name=_("Top Role"),
                    value=TextFormat.blockquotes(member.top_role.mention),
                )
                embed.add_field(
                    name=_("Server Owner"),
                    value=TextFormat.blockquotes(tick[member == member.guild.owner]),
                )

        flags: set[PublicUserFlags] = set(
            [flag for flag, has in user.public_flags if has]
        )

        if user.display_avatar.is_animated() or user.banner:
            flags.add("subscriber")
        badges = [
            str(menu.bot.get_emoji_local("badges", badge)) for badge in flags
        ] or [tick[False]]

        more: Dict[str, str] = {
            (_("#Tag"), ":"): TextFormat.codeblock(user.discriminator),
            (_("ID"), ":"): TextFormat.codeblock(user.id),
            (_("Created"), ":"): str(format_dt(user.created_at, "R")),
            (_("Shared Servers"), ":"): TextFormat.codeblock(
                len(user.mutual_guilds) if hasattr(user, "mutual_guilds") else _("None")
            ),
            (_("Badges"), ":"): " ".join(badges),
        }

        embed.add_field(
            name=_("More Information"),
            value=TextFormat.multiblockquotes(
                "\n".join(
                    TextFormat.bold(str(k) + str(s) + " " + str(v))
                    for (k, s), v in more.items()
                )
            ),
            inline=False,
        )

        if banner := getattr(user, "banner", None):
            embed.set_image(url=banner.url)
        else:
            embed.add_field(
                name="\u200b",
                value=TextFormat.blockquotes(menu.bot.config.embed.footer),
                inline=False,
            )
        return embed, None


class ActivitieSource(ItemPageSource):
    user: Member

    def __init__(self, ctx: ShakeContext | Interaction, user: Member, *args, **kwargs):
        self.user: Member = user
        super().__init__(
            ctx,
            item=user.activities,
            title=MISSING,
            label=_("Activities"),
            paginating=True,
            per_page=10,
            *args,
            **kwargs,
        )

    def format_page(
        self, menu: Menu, item: Tuple[ActivityTypes, ...], **kwargs: Any
    ) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("User Activities"))
        prefix = str(PartialEmoji(name="dot", id=1093146860182568961)) + ""
        for activity in item:
            index = self.item[activity]
            i = self.item.index(activity) + 1
            _type = {
                "online": _("online"),
                "offline": _("offline"),
                "streaming": _("streaming"),
                "idle": _("idle"),
                "dnd": _("dnd"),
            }.get(str(type.name), str(type.name))

            to_long = len(str(activity.name)) > 31

            _name = activity.name[0:28] + "[...]" if to_long else activity.name
            _name = f"„{_name}“".lower() if type.value == 4 else _name

            embed.add_field(
                name=prefix
                + _("Top {index} Activity ({type})").format(
                    _="`", index="`" + str(i) + "`", type=_type
                ),
                value="**({}):** ".format(index) + _name,
            )
            if (item.index((type, activity.name)) + 1) % 2 == 0:
                embed.add_field(name=f"\u200b", value="\u200b", inline=True)
        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed


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
        return embed
