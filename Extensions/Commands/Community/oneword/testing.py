from enum import Enum
from typing import Dict, List, Optional

from discord import (
    ButtonStyle,
    ChannelType,
    Forbidden,
    Guild,
    HTTPException,
    Interaction,
    PartialEmoji,
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
    Slash,
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


class OneWordMenu(ForwardingMenu):
    react: bool = MISSING
    channel: Optional[TextChannel] = MISSING

    def __init__(self, ctx):
        super().__init__(ctx)
        finish = ForwardingFinishSource(self)
        finish.previous = React

        self.sites = [Channel(self), React(self), finish]


class Channel(ForwardingSource):
    view: OneWordMenu
    channel: Optional[TextChannel]
    select = ChannelSelect(
        channel_types=[ChannelType.text], placeholder="Select a TextChannel!", row=1
    )
    button = Button(label=_("Create one"), style=ButtonStyle.green, row=4)

    def __init__(self, view: OneWordMenu) -> None:
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
        if not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("OneWord channel"))
        embed.title = _("Choose in which text channel this game should be!")
        points = [
            _("You can set up an existing text channel from your server."),
            _(
                "Alternatively, you have the option to have a new text channel created for it."
            ),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can go back here in the setup to change settings..")
        )
        return {"embed": embed}


class React(ForwardingSource):
    view: OneWordMenu
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

    def __init__(self, view: OneWordMenu) -> None:
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

        if not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("OneWord bot reactions"))
        embed.title = _("Decide if I am allowed to react to the posts in the game")

        points = [
            _(
                "You can allow me reactions so that users know directly whether posts are accepted as correct."
            ),
            _("You can also deny my reactions to suppress the spam of reactions."),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can go back here in the setup to change settings..")
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
                query = "SELECT guild_id, count FROM oneword;"
            else:
                query = "SELECT user_id, SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS count FROM onewords GROUP BY user_id;"
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

    async def setup(
        self,
    ):
        menu = OneWordMenu(ctx=self.ctx)
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
                    name="oneword", slowmode_delay=5
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
            query = "SELECT * FROM counting WHERE channel_id = $1"
            record = await connection.fetchrow(query, channel.id)
            if record:
                embed = embed.to_error(
                    self.ctx,
                    description=_(
                        "In {channel} is already a Counting game set up. Aborting..."
                    ).format(channel=channel.mention),
                )
                await message.edit(embed=embed, view=None)
                return False

            query = 'INSERT INTO "oneword" (channel_id, guild_id, react) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING'
            await connection.execute(query, channel.id, self.ctx.guild.id, react)

        embed = embed.to_success(
            ctx=self.ctx,
            description=_("{game} is successfully set up in {channel}!").format(
                game="OneWord", channel=channel.mention
            ),
        )
        embed.set_footer(text=_("Note: You can freely edit the text channel now."))

        await message.edit(
            embed=embed,
            view=None,
        )

    async def info(self) -> None:
        slash = await Slash(self.ctx.bot).__await__(self.ctx.bot.get_command("oneword"))

        setup = self.ctx.bot.get_command("oneword setup")
        cmd, setup = await slash.get_sub_command(setup)

        embed = ShakeEmbed()
        embed.title = Format.blockquotes(_("Welcome to „OneWord“"))
        embed.description = (
            Format.italics(
                _("Thanks for your interest in the game in this awesome place!")
            )
            + " "
            + str(PartialEmoji(name="wumpus", id=1114674858706616422))
        )
        embed.add_field(
            name=_("How to setup the game?"),
            value=_(
                "Get started by using the command {command} to create and setup the essential channel"
            ).format(command=setup),
            inline=False,
        )
        embed.add_field(
            name=_("How to use the game?"),
            value=_(
                "This game is all about words, which are posted one after the other in the chat to create a creative sentance"
            ),
            inline=False,
        )
        rules = [
            _("One person can't post words in a row (others are required)."),
            _("The sentance is done with punctuation marks (eg. „!“)."),
            _("No botting, if you have failed to often, you'll get muted."),
            _("There is no failing."),
        ]
        embed.add_field(
            name=_("OneWord rules"),
            value="\n".join(Format.list(_) for _ in rules),
            inline=False,
        )
        embed.add_field(
            name=_("How to configure the game?"),
            value=_("Currently there is nothing to configure!"),
            inline=False,
        )
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png"
        )
        await self.ctx.chat(embed=embed, ephemeral=True)


#
############
