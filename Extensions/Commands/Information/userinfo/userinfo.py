############
#
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, get_args

from discord import (
    Asset,
    Colour,
    Guild,
    Interaction,
    Member,
    PublicUserFlags,
    Role,
    User,
)
from discord.activity import ActivityType, ActivityTypes, Spotify
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
from Classes.types import Format, Types
from Classes.useful import MISSING
from Extensions.Commands.Information.serverinfo.serverinfo import Front as SiFront

########
#
placements = {1: "🥇", 2: "🥈", 3: "🥉"}
########
#


class command(ShakeCommand):
    def __init__(
        self,
        ctx,
        user: User,
        member: Optional[Member] = None,
        fallback: Optional[Member] = None,
    ):
        super().__init__(ctx)
        self.user: User = user
        self.member: Optional[Member] = member
        self.fallback: Optional[Member] = fallback

    async def __await__(self):
        select = CategoricalSelect(self.ctx, source=SourceSource)
        menu = Menu(
            ctx=self.ctx,
            source=Front(),
            user=self.user,
            member=self.member,
            fallback=self.fallback,
            select=select,
        )

        categories = {}

        if self.user.bot:
            counting = aboveme = oneword = False
        else:
            async with self.bot.gpool.acquire() as connection:
                query = """SELECT 
                    EXISTS (SELECT 1 FROM countings WHERE user_id = $1 LIMIT 1),
                    EXISTS (SELECT 1 FROM abovemes WHERE user_id = $1 LIMIT 1),
                    EXISTS (SELECT 1 FROM onewords WHERE user_id = $1 LIMIT 1);
                """
                counting, aboveme, oneword = await connection.fetchrow(
                    query, self.user.id
                )

        if bool(counting):
            categories[CountingSource(ctx=self.ctx, user=self.user)] = 1

        if bool(oneword):
            categories[OneWordSource(ctx=self.ctx, user=self.user)] = 1

        if bool(aboveme):
            categories[AboveMeSource(ctx=self.ctx, user=self.user)] = 1

        if bool(self.user.mutual_guilds):
            categories[MutualSource(ctx=self.ctx, user=self.user)] = 1

        flags = [has is True for flag, has in self.user.public_flags]
        if any(flags):
            categories[BadgesSource(ctx=self.ctx, user=self.user)] = 1

        assets = [
            getattr(self.member or self.user, "avatar"),
            getattr(self.member or self.user, "display_avatar"),
            getattr(self.member, "guild_avatar", None),
            getattr(self.user, "banner"),
        ]
        if any(_ is not None for _ in assets):
            categories[
                AssetsSource(ctx=self.ctx, user=self.user, got=assets)
            ] = self.user.display_avatar

        if self.member:
            member = {
                RolesSource(ctx=self.ctx, member=self.member): set(self.member.roles),
                PositionSource(ctx=self.ctx, member=self.member): list(
                    self.member.guild.members
                ),
                ActivitiesSource(
                    ctx=self.ctx, member=self.member
                ): self.member.activities,
                PermissionsSource(ctx=self.ctx, member=self.member): list(
                    self.member.guild_permissions
                ),
            }
            categories = categories | member

        menu.add_categories(categories=categories)
        if await menu.setup():
            await menu.send(ephemeral=True)


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
            name=self.user.name,
            icon_url=getattr(self.user.avatar, "url", recovery),
            url=f"https://discordapp.com/users/{self.user.id}",
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
                "ID:": Format.codeblock(role.id),
                _("Created") + ":": str(format_dt(role.created_at, "f")),
                _("Mention") + ":": role.mention if is_member else "@" + role.name,
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


class AssetsSource(ListPageSource):
    guild: Guild
    got: Dict[Asset, str]

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
        self.assets = {
            self.member.avatar if self.member else self.user.avatar: _("User's Avatar"),
            getattr(self.member or self.user, "display_avatar", None): _(
                "User's Display Avatar"
            ),
            self.member.guild_avatar if self.member else None: _("User's Guild Avatar"),
            self.user.banner: _("User's Banner"),
        }

        super().__init__(
            ctx,
            items=list(x for x in self.assets.keys() if x),
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
            title=self.assets[items], description=avatars if bool(avatars) else None
        )
        embed.set_image(url=items.url)
        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed, None


class MutualSource(ListPageSource):
    guild: Guild
    got: Dict[Asset, str]

    def __init__(
        self,
        ctx: ShakeContext | Interaction,
        user: User,
        *args,
        **kwargs,
    ):
        self.user: User = user
        guilds: Optional[Member] = user.mutual_guilds

        super().__init__(
            ctx,
            items=list(guilds),
            title=MISSING,
            label=_("Mutual Servers"),
            paginating=True,
            per_page=1,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: Guild, **kwargs: Any) -> ShakeEmbed:
        embed = SiFront().guild(menu.ctx, items)
        embed.title = str(items.name)
        embed.set_footer(
            text=_("Guild {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )

        return embed, None


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
            value=Format.blockquotes(
                Format.bold(
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
            value=Format.blockquotes(
                Format.bold(format_dt(self.member.joined_at, style="F"))
            ),
        )

        index = self.item.index(self.member)

        lower = max(0, index - 6)
        upper = min(len(self.item) - 1, index + 6) + 1
        selected: List[Member] = self.item[lower:upper]

        embed.add_field(
            name="\u200b",
            value=Format.multicodeblock(
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
        return embed, None


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

        embed.description = "\n".join(
            Format.list(
                Format.join(
                    str(self.ctx.bot.get_emoji_local("badges", property)),
                    *list(
                        x.capitalize() for x in str(property).replace("_", " ").split()
                    ),
                )
            )
            for property in set(flag for flag, has in flags if has)
        )

        return embed, None


class CountingSource(ItemPageSource):
    user: User

    def __init__(self, ctx: ShakeContext | Interaction, user: User, *args, **kwargs):
        self.user: User = user
        super().__init__(
            ctx,
            item=user,
            title=MISSING,
            label=_("Counting"),
            *args,
            **kwargs,
        )

    async def fetch(self) -> int:
        async with self.bot.gpool.acquire() as connection:
            query = """SELECT
                    SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) AS failed, 
                    SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS passed,
                    (
                        SELECT MAX(count) AS highest FROM countings WHERE user_id = $1 AND direction = true AND failed = false GROUP BY user_id
                    ),
                    (
                        SELECT used FROM countings WHERE user_id = $1 AND failed = false ORDER BY used DESC LIMIT 1
                    ) AS latest,
                    (
                        WITH ranked AS (
                            SELECT user_id, ROW_NUMBER() OVER (ORDER BY SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) - SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) DESC) AS position FROM countings GROUP BY user_id
                        )
                        SELECT position FROM ranked WHERE user_id = $1
                    )
                FROM countings
                WHERE user_id = $1
                GROUP BY user_id;
            """
            (
                self.failed,
                self.passed,
                self.highest,
                self.latest,
                self.placement,
            ) = await connection.fetchrow(query, self.user.id)

    @property
    def sum(self) -> int:
        return self.failed + self.passed

    @property
    def score(self) -> int:
        return self.passed - self.failed

    @property
    def rate(self) -> float:
        return round(self.passed * 100 / self.sum, 2)

    async def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        if any(
            not hasattr(self, _)
            for _ in set(("failed", "passed", "highest", "latest", "placement"))
        ):
            await self.fetch()

        embed = ShakeEmbed(title=_("Counting stats"))

        embed.description = Format.bold(
            _("{user} scored a total of {score} valid counts (#{placement})").format(
                user=self.user.mention,
                score=self.score,
                placement=Format.join(
                    str(self.placement), placements.get(self.placement, "")
                ),
            )
        )

        embed.add_field(
            name=_("Total passed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.passed, self.sum))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total failed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.failed, self.sum))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total rate"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(str(round(self.rate, 2)) + "%", "css")
                )
            ),
        )

        embed.add_field(
            name=_("Total last played"),
            value=Format.multiblockquotes(
                Format.join(
                    format_dt(self.latest.replace(tzinfo=timezone.utc), "F"),
                    "("
                    + format_dt(self.latest.replace(tzinfo=timezone.utc), "R")
                    + ")",
                )
            ),
            inline=False,
        )

        embed.add_field(
            name=_("Total highest count"),
            value=Format.multiblockquotes(Format.multicodeblock(self.highest, "css")),
        )

        embed.set_footer(text=_("Information can update with time"))

        return embed, None


class OneWordSource(ItemPageSource):
    user: User

    def __init__(self, ctx: ShakeContext | Interaction, user: User, *args, **kwargs):
        self.user: User = user
        super().__init__(
            ctx,
            item=user,
            title=MISSING,
            label=_("OneWord"),
            *args,
            **kwargs,
        )

    async def fetch(self):
        async with self.bot.gpool.acquire() as connection:
            query = """SELECT
                    SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) AS failed, 
                    SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS passed,
                    (
                        SELECT used FROM countings WHERE user_id = $1 AND failed = false ORDER BY used DESC LIMIT 1
                    ) AS latest,
                    (
                        WITH ranked AS (
                            SELECT user_id, ROW_NUMBER() OVER (ORDER BY SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) - SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) DESC) AS position FROM countings GROUP BY user_id
                        )
                        SELECT position FROM ranked WHERE user_id = $1
                    )
                FROM onewords
                WHERE user_id = $1
                GROUP BY user_id;
            """
            (
                self.failed,
                self.passed,
                self.latest,
                self.placement,
            ) = await connection.fetchrow(query, self.user.id)

    async def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        if any(
            not hasattr(self, _)
            for _ in set(("failed", "passed", "latest", "placement"))
        ):
            await self.fetch()

        embed = ShakeEmbed(title=_("OneWord stats"))

        summed: int = self.failed + self.passed
        score: int = self.passed - self.failed
        rate: float = self.passed * 100 / summed

        embed.description = Format.bold(
            _("{user} scored a total of {score} valid counts (#{placement})").format(
                user=self.user.mention,
                score=score,
                placement=Format.join(
                    str(self.placement), placements.get(self.placement, "")
                ),
            )
        )

        embed.add_field(
            name=_("Total passed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.passed, summed))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total failed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.failed, summed))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total rate"),
            value=Format.multiblockquotes(
                Format.bold(Format.multicodeblock(str(round(rate, 2)) + "%", "css"))
            ),
        )

        embed.add_field(
            name=_("Total last played"),
            value=Format.multiblockquotes(
                Format.join(
                    format_dt(self.latest.replace(tzinfo=timezone.utc), "F"),
                    "("
                    + format_dt(self.latest.replace(tzinfo=timezone.utc), "R")
                    + ")",
                )
            ),
        )

        embed.set_footer(text=_("Information can update with time"))

        return embed, None


class AboveMeSource(ItemPageSource):
    user: User

    def __init__(self, ctx: ShakeContext | Interaction, user: User, *args, **kwargs):
        self.user: User = user
        super().__init__(
            ctx,
            item=user,
            title=MISSING,
            label=_("AboveMe"),
            *args,
            **kwargs,
        )

    async def fetch(self):
        async with self.bot.gpool.acquire() as connection:
            query = """SELECT
                    SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) AS failed, 
                    SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS passed,
                    (
                        SELECT phrase FROM abovemes WHERE user_id = $1 AND failed = false AND phrase IS NOT NULL ORDER BY LENGTH(phrase) DESC LIMIT 1
                    ) AS longest,
                    (
                        SELECT used FROM abovemes WHERE user_id = $1 AND failed = false ORDER BY used DESC LIMIT 1
                    ) AS latest,
                    (
                        WITH ranked AS (
                            SELECT user_id, ROW_NUMBER() OVER (ORDER BY SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) - SUM(CASE WHEN failed = true THEN 1 ELSE 0 END) DESC) AS position FROM countings GROUP BY user_id
                        )
                        SELECT position FROM ranked WHERE user_id = $1
                    )
                FROM abovemes
                WHERE user_id = $1
                GROUP BY user_id;
            """
            (
                self.failed,
                self.passed,
                self.longest,
                self.latest,
                self.placement,
            ) = await connection.fetchrow(query, self.user.id)

    async def format_page(self, menu: Menu, *args: Any, **kwargs: Any) -> ShakeEmbed:
        if any(
            not hasattr(self, _)
            for _ in set(("failed", "passed", "longest", "latest", "placement"))
        ):
            await self.fetch()
        embed = ShakeEmbed(title=_("AboveMe stats"))

        summed: int = self.failed + self.passed
        score: int = self.passed - self.failed
        rate: float = self.passed * 100 / summed

        embed.description = Format.bold(
            _("{user} scored a total of {score} valid phrases (#{placement})").format(
                user=self.user.mention,
                score=score,
                placement=Format.join(
                    str(self.placement), placements.get(self.placement, "")
                ),
            )
        )

        embed.add_field(
            name=_("Total passed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.passed, summed))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total failed"),
            value=Format.multiblockquotes(
                Format.bold(
                    Format.multicodeblock(
                        Format.join("/".join(str(_) for _ in (self.failed, summed))),
                        "css",
                    )
                )
            ),
        )

        embed.add_field(
            name=_("Total rate"),
            value=Format.multiblockquotes(
                Format.bold(Format.multicodeblock(str(round(rate, 2)) + "%", "css"))
            ),
        )

        embed.add_field(
            name=_("Total last played"),
            value=Format.multiblockquotes(
                Format.join(
                    format_dt(self.latest.replace(tzinfo=timezone.utc), "F"),
                    "("
                    + format_dt(self.latest.replace(tzinfo=timezone.utc), "R")
                    + ")",
                )
            ),
            inline=False,
        )

        embed.add_field(
            name=_("Total longest sentance"),
            value=Format.multiblockquotes(Format.multicodeblock(self.longest, "css")),
            inline=False,
        )

        embed.set_footer(text=_("Information can update with time"))

        return embed, None


class PermissionsSource(ListPageSource):
    guild: Guild
    got: Dict[Asset, str]

    def __init__(
        self,
        ctx: ShakeContext | Interaction,
        member: Member = None,
        *args,
        **kwargs,
    ):
        self.member: Optional[Member] = member

        super().__init__(
            ctx,
            items=member.guild_permissions,
            title=MISSING,
            label=_("Permissions"),
            paginating=True,
            per_page=6,
            *args,
            **kwargs,
        )

    def format_page(self, menu: Menu, items: Asset, **kwargs: Any) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Members server permissions"))

        embed.description = "\n".join(
            Format.list(
                " ".join(
                    list(
                        _.capitalize()
                        for _ in str(permission).replace("_", " ").split()
                    )
                )
            )
            for permission, has in items
            if has
        )

        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed, None


class ActivitiesSource(ItemPageSource):
    member: Member

    def __init__(
        self, ctx: ShakeContext | Interaction, member: Member, *args, **kwargs
    ):
        self.member: Member = member
        filtered = list(filter(lambda a: a.type.value != 4, member.activities))

        types = set(activity.type for activity in filtered)

        activities = {
            atype: list(filter(lambda a: a.type == atype, filtered)) for atype in types
        }

        super().__init__(
            ctx,
            item=activities,
            title=MISSING,
            label=_("Activities"),
            *args,
            **kwargs,
        )

    def format_page(
        self, menu: Menu, items: Tuple[ActivityType, str], **kwargs: Any
    ) -> ShakeEmbed:
        embed = ShakeEmbed(title=_("Member Activities"))

        self.item: Dict[ActivityType, Tuple[ActivityTypes, ...]]
        for type, activities in self.item.items():
            type = Format.join(
                str(type.name).capitalize(),
                "...",
            )
            values = list()
            for activity in activities:
                if isinstance(activity, Spotify):
                    values.append(
                        _("to {name} by {author} on Spotify").format(
                            name=Format.bold(activity.title),
                            author=Format.bold(", ".join(activity.artists)),
                        )
                    )
                else:
                    values.append(activity.name)

            embed.add_field(
                name=type,
                value="\n".join(
                    Format.list(Format.join("...", value)) for value in values
                ),
                inline=False,
            )

        embed.set_footer(
            text=_("Page {page} of {pages}").format(
                page=menu.page + 1, pages=self.maximum
            )
        )
        return embed, None


class Front(FrontPageSource):
    def format_page(self, menu: Menu, items: Any):
        user: User = menu.user
        member: Optional[Member] = menu.member
        fallback: Optional[Member] = menu.fallback
        embed = ShakeEmbed.default(menu.ctx, title=_("General Overview"))

        recovery = "https://cdn.discordapp.com/attachments/946862628179939338/1093165455289622632/no_face_2.png"
        embed.set_thumbnail(url=getattr(user.avatar, "url", recovery))

        # embed.add_field(name=_("Joined Discord"), value=Format.blockquotes(format_dt(user.created_at, style="F")))
        embed.add_field(
            name=_("Bot"),
            value=Format.blockquotes(
                (menu.bot.emojis.no, menu.bot.emojis.yes)[user.bot]
            ),
        )
        embed.add_field(
            name=_("Discord System"),
            value=Format.blockquotes(
                (menu.bot.emojis.no, menu.bot.emojis.yes)[user.system]
            ),
        )
        embed.add_field(
            name=_("Member"),
            value=Format.blockquotes(
                (menu.bot.emojis.no, menu.bot.emojis.yes)[bool(member)]
            ),
        )

        if m := member or fallback:
            for activity in filter(lambda a: a.type.value == 4, m.activities):
                if getattr(activity, "name", None):
                    embed.description = "„" + activity.name + "“"
                    break

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
                value=Format.blockquotes(Format.bold(status)) + " " + emoji,
            )
            if member:
                embed.add_field(
                    name=_("Top Role"),
                    value=Format.blockquotes(member.top_role.mention),
                )
                embed.add_field(
                    name=_("Server Owner"),
                    value=Format.blockquotes(
                        (menu.bot.emojis.no, menu.bot.emojis.yes)[
                            member == member.guild.owner
                        ]
                    ),
                )

        embed.add_field(
            name=_("Created"),
            value=Format.multiblockquotes(
                Format.join(
                    format_dt(user.created_at, "F"),
                    "(" + format_dt(user.created_at, "R") + ")",
                )
            ),
            inline=False,
        )

        flags: set[PublicUserFlags] = set(
            [flag for flag, has in user.public_flags if has]
        )

        if user.display_avatar.is_animated() or user.banner:
            flags.add("subscriber")
        badges = [
            str(menu.bot.get_emoji_local("badges", badge)) for badge in flags
        ] or [(menu.bot.emojis.no, menu.bot.emojis.yes)[False]]

        more: Dict[str, str] = {
            (_("Display name"), ":"): Format.codeblock(user.global_name),
            (_("#Tag"), ":"): Format.codeblock(
                _("Migrated to username")
                if user.discriminator == "0"
                else user.discriminator
            ),
            (_("ID"), ":"): Format.codeblock(user.id),
            (_("Shared Servers"), ":"): Format.codeblock(
                len(user.mutual_guilds) if hasattr(user, "mutual_guilds") else _("None")
            ),
            (_("Badges"), ":"): " ".join(badges),
        }

        embed.add_field(
            name=_("More Information"),
            value=Format.multiblockquotes(
                "\n".join(
                    Format.bold(str(k) + str(s) + " " + str(v))
                    for (k, s), v in more.items()
                )
            ),
            inline=False,
        )

        if banner := getattr(user, "banner", None):
            embed.set_image(url=banner.url)
        else:
            embed.advertise(menu.bot)
        return embed, None


features = (
    RolesSource
    | BadgesSource
    | AssetsSource
    | PositionSource
    | PermissionsSource
    | ActivitiesSource
    | CountingSource
    | MutualSource
    | AboveMeSource
    | OneWordSource
)
