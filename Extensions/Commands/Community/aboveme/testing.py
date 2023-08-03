from enum import Enum
from typing import Dict, List, Optional

from discord import (
    ButtonStyle,
    ChannelType,
    Forbidden,
    Guild,
    HTTPException,
    Interaction,
    SelectOption,
    TextChannel,
)
from discord.app_commands import AppCommandChannel
from discord.ui import Button, ChannelSelect, Select

from Classes import (
    MISSING,
    Format,
    ShakeCommand,
    ShakeContext,
    ShakeEmbed,
    UserGuild,
    _,
)
from Classes.accessoires import (
    ForwardingFinishSource,
    ForwardingMenu,
    ForwardingSource,
    ListPageSource,
    ShakePages,
)

############
#


class Permission(Enum):
    allow = True
    deny = False


class AboveMeMenu(ForwardingMenu):
    react: bool = MISSING
    channel: Optional[TextChannel] = MISSING

    def __init__(self, ctx):
        super().__init__(ctx)
        finish = ForwardingFinishSource(self)
        finish.previous = React

        self.sites = [Channel(self), React(self), finish]


class Channel(ForwardingSource):
    view: AboveMeMenu
    channel: Optional[TextChannel]
    select = ChannelSelect(
        channel_types=[ChannelType.text], placeholder="Select a TextChannel!", row=1
    )
    button = Button(label=_("Create one"), style=ButtonStyle.green, row=4)

    def __init__(self, view: AboveMeMenu) -> None:
        super().__init__(
            view=view,
            previous=None,
            next=React,
            items=[self.select, self.button, view.cancel],
        )

    async def __call__(self, interaction: Interaction) -> None:
        if bool(self.select.values):
            value = self.select.values[0]
        else:
            value = None
        await self.callback(interaction, value)

    async def callback(
        self, interaction: Interaction, value: Optional[AppCommandChannel] = None
    ):
        if isinstance(value, AppCommandChannel):
            value = self.bot.get_channel(value.id)
        self.view.channel = value
        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("AboveMe channel"))
        embed.title = _("Choose in which text channel this game should be!")
        points = [
            _("You can set up an existing text channel from your server."),
            _(
                "Alternatively, you have the option to have a new text channel created for it."
            ),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class React(ForwardingSource):
    view: AboveMeMenu
    react: Permission
    item = Select(
        options=[
            SelectOption(
                label="Allow Shake to react",
                description=None,
                value=Permission.allow.name,
            ),
            SelectOption(
                label="Forbid Shake to react",
                description=None,
                value=Permission.deny.name,
            ),
        ],
        placeholder="Decide between these two options...",
        row=1,
    )

    def __init__(self, view: AboveMeMenu) -> None:
        self.item.callback = self.__call__
        super().__init__(
            view=view,
            previous=Channel,
            next=MISSING,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: Permission):
        self.view.react = Permission[value].value

        finish = ForwardingFinishSource(self.view)
        finish.previous = React
        await self.view.show_source(source=finish, rotation=1)

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("AboveMe bot reactions"))
        embed.title = _("Decide if I am allowed to react to the posts in the game")

        points = [
            _(
                "You can allow me reactions so that users know directly whether posts are accepted as correct."
            ),
            _("You can also deny my reactions to suppress the spam of reactions."),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class Page(ListPageSource):
    def __init__(
        self,
        ctx: ShakeContext,
        title: str,
        items: Dict[Guild, int],
        description: str | None = ...,
        label: str | None = ...,
    ):
        self.from_dict: Dict[Guild, int] = items
        items = list(
            _
            for _ in dict(
                sorted(items.items(), key=lambda x: x[1], reverse=True)
            ).keys()
            if _
        )
        super().__init__(ctx, items, title, None, description, True, 10, label)

    async def format_page(self, menu, items: list[Guild]):
        embed = ShakeEmbed()
        embed.title = self.title
        embed.description = "\n".join(
            [
                "{} {}, {}".format(
                    Format.bold("#" + str(items.index(item) + 1)),
                    Format.codeblock(item.name),
                    Format.bold(self.from_dict[item]),
                )
                for item in items
            ]
        )
        return embed, None


class command(ShakeCommand):
    async def score(self, type: str) -> None:
        await self.ctx.defer()
        try:
            type = UserGuild[type.lower()].value
        except KeyError:
            type = Guild
        is_guild = type == Guild
        async with self.bot.gpool.acquire() as connection:
            if is_guild:
                query = "SELECT guild_id, count FROM aboveme;"
            else:
                query = "SELECT user_id, SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS count FROM abovemes GROUP BY user_id;"
                # highest = "SELECT user_id, MAX(count) AS highest FROM countings GROUP BY user_id;"
            counters: List[int, int] = await connection.fetch(query)

        items = {
            self.bot.get_guild(_id)
            if is_guild
            else await self.bot.get_user_global(_id): score
            for _id, score in counters
        }

        title = (
            Format.italics(_("CURRENT SERVER SCORES"))
            if is_guild
            else Format.italics(_("CURRENT USER SCORES"))
        )

        source = Page(
            self.ctx,
            title=title,
            items=items,
        )
        menu = ShakePages(source, self.ctx)
        await menu.setup()
        await menu.send(ephemeral=True)
        pass

    async def setup(
        self,
    ):
        menu = AboveMeMenu(ctx=self.ctx)
        message = await menu.setup(menu.sites)
        await menu.wait()

        embed = ShakeEmbed(timestamp=None)

        channel = menu.channel
        react = menu.react

        if menu.timeouted or any(_ is MISSING for _ in (channel, react)):
            return

        if channel is None:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="aboveme", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                embed = embed.to_error(
                    self.ctx,
                    description=_("I could not create a TextChannel. Aborting..."),
                )
                await message.edit(embed=embed, view=None)
                return False

        else:
            if channel.slowmode_delay == 0:
                try:
                    await channel.edit(slowmode_delay=5)
                except (HTTPException, Forbidden):
                    embed = embed.to_error(
                        self.ctx,
                        description=_("I could not edit the TextChannel! Aborting..."),
                    )
                    await message.edit(embed=embed, view=None)
                    return False

        async with self.ctx.db.acquire() as connection:
            query = "SELECT * FROM aboveme WHERE channel_id = $1"
            record = await connection.fetchrow(query, channel.id)
            if record:
                embed = embed.to_error(
                    self.ctx,
                    description=_(
                        "There is already a game set up in {channel}. Aborting..."
                    ).format(channel=channel.mention),
                )
                await message.edit(embed=embed, view=None)
                return False

            query = 'INSERT INTO "aboveme" (channel_id, guild_id, react) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING'
            await connection.execute(query, channel.id, self.ctx.guild.id, react)

        embed = embed.to_success(
            ctx=self.ctx,
            description=_("{game} is successfully set up in {channel}!").format(
                game="AboveMe", channel=channel.mention
            ),
        )
        embed.set_footer(text=_("Note: You can freely edit the text channel now."))

        await message.edit(
            embed=embed,
            view=None,
        )


#
############
