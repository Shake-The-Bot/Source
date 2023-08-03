from collections import deque
from enum import Enum
from typing import Dict, List, Optional

from discord import (
    ButtonStyle,
    ChannelType,
    Forbidden,
    Guild,
    HTTPException,
    Interaction,
    Message,
    PartialEmoji,
    SelectOption,
    TextChannel,
    TextStyle,
    Webhook,
)
from discord.app_commands import AppCommandChannel
from discord.components import SelectOption
from discord.ui import Button, ChannelSelect, Modal, Select, TextInput
from discord.utils import MISSING

from Classes import MISSING, Format, ShakeCommand, ShakeEmbed, Slash, UserGuild, _
from Classes.accessoires import (
    ForwardingFinishSource,
    ForwardingMenu,
    ForwardingSource,
    ListPageSource,
    ShakePages,
)
from Classes.helpful import ShakeContext, ShakeEmbed

############
#

previousemoji = PartialEmoji(name="left", id=1033551843210579988)


class Directions(Enum):
    up = True
    down = False


class MessageTypes(Enum):
    webhook = Webhook
    botuser = Message


class Permission(Enum):
    allow = True
    deny = False


class CountingMenu(ForwardingMenu):
    start: Optional[int] = MISSING
    goal: Optional[int] = MISSING
    direction: Directions = MISSING
    numbers: Permission = MISSING
    math: Permission = MISSING
    message_type: MessageTypes = MISSING
    react: Permission = MISSING
    channel: Optional[TextChannel] = MISSING

    def __init__(self, ctx):
        super().__init__(ctx)
        finish = ForwardingFinishSource(self)
        finish.previous = React

        self.sites = [
            Channel(self),
            Direction(self),
            Number(self),
            Math(self),
            MessageType(self),
            React(self),
            finish,
        ]


class Channel(ForwardingSource):
    view: CountingMenu
    channel: Optional[TextChannel]
    select = ChannelSelect(
        channel_types=[ChannelType.text], placeholder="Select a TextChannel!", row=1
    )
    button = Button(label=_("Create one"), style=ButtonStyle.green, row=4)

    def __init__(self, view: CountingMenu) -> None:
        super().__init__(
            view=view,
            previous=None,
            next=Direction,
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
        embed.set_author(name=_("Counting channel"))
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


class Direction(ForwardingSource):
    view: CountingMenu
    direction: Directions
    item = Select(
        options=[
            SelectOption(label="Count Up", description=None, value=Directions.up.name),
            SelectOption(
                label="Count Down", description=None, value=Directions.down.name
            ),
        ],
        placeholder="Choose the game direction...",
        row=1,
    )

    def __init__(self, view: CountingMenu) -> None:
        super().__init__(
            view=view,
            previous=Channel,
            next=Number,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: Directions):
        self.view.direction = Directions[value].value

        if self.view.direction == Directions.up.value:
            self.view.start = 0
            await interaction.response.send_modal(GoalModal(self, self.view))
        else:
            self.view.goal = None
            await interaction.response.send_modal(StartModal(self, self.view))

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Counting direction"))
        embed.title = _("Choose in which direction Counting should go!")
        points = [
            _(
                "You can start counting at the number 1 and continue {game} in ascending order."
            ).format(game=Format.bold("Counting")),
            _(
                "Alternatively, you can specify a starting point from which {game} starts in descending order."
            ).format(game=Format.bold("Counting")),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class Number(ForwardingSource):
    view: CountingMenu
    numbers: Permission
    item = Select(
        options=[
            SelectOption(
                label="Allow text messages (comments) in Counting",
                description=None,
                value=Permission.allow.name,
            ),
            SelectOption(
                label="Deny text messages (comments) in Counting",
                description=None,
                value=Permission.deny.name,
            ),
        ],
        placeholder="Text messages often create a little more clutter",
        row=1,
    )

    def __init__(self, view: CountingMenu) -> None:
        super().__init__(
            view=view,
            previous=Direction,
            next=Math,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: Permission):
        self.view.numbers = not Permission[value].value

        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Counting rules"))
        embed.title = _("Decide if text messages are allowed in Counting")
        points = [
            _("You can allow text messages so that members can comment to each other."),
            _("You can deny text messages so that {game} remains clearer.").format(
                game=Format.bold("Counting")
            ),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class Math(ForwardingSource):
    view: CountingMenu
    math: Permission
    item = Select(
        options=[
            SelectOption(
                label="Allow mathematical calculations in Counting",
                description=None,
                value=Permission.allow.name,
            ),
            SelectOption(
                label="Deny mathematical calculations in Counting",
                description=None,
                value=Permission.deny.name,
            ),
        ],
        placeholder="Calculations expand the spectrum of possibilities",
        row=1,
    )

    def __init__(self, view: CountingMenu) -> None:
        super().__init__(
            view=view,
            previous=Number,
            next=React,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: Permission):
        self.view.math = Permission[value].value

        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Counting ways"))
        embed.title = _("Decide if mathematical calculations are allowed in Counting")
        points = [
            _(
                "You can allow mathematical calculations so that members can find new ways."
            ),
            _(
                "You can deny mathematical calculations so that {game} remains clearer."
            ).format(game=Format.bold("Counting")),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings.")
        )
        return {"embed": embed}


class MessageType(ForwardingSource):
    view: CountingMenu
    item = Select(
        options=[
            SelectOption(
                label="Get responses via custom Webhook",
                description=None,
                value=MessageTypes.webhook.name,
            ),
            SelectOption(
                label="Get responses via Shake",
                description=None,
                value=MessageTypes.botuser.name,
            ),
        ],
        placeholder="Decide between these two options...",
        row=1,
    )

    def __init__(self, view: CountingMenu) -> None:
        self.item.callback = self.__call__
        super().__init__(
            view=view,
            previous=Math,
            next=React,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: MessageTypes):
        self.view.message_type = MessageTypes[value].value

        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Counting bot responses"))
        embed.title = _("Decide in which way I should response to fails, edits, etc.")

        points = [
            _(
                "You can let me send the responses via webhooks that will make the whole thing look more natural"
            ),
            _(
                "You can also let me send all messages as a user, to create an easier overview of the actions."
            ),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class React(ForwardingSource):
    view: CountingMenu
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

    def __init__(self, view: CountingMenu) -> None:
        self.item.callback = self.__call__
        super().__init__(
            view=view,
            previous=MessageType,
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
        embed.set_author(name=_("Counting bot reactions"))
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


class GoalModal(Modal):
    def __init__(self, source: Direction, view: CountingMenu) -> None:
        self.source = source
        self.view = view
        super().__init__(title="Goal")

    goal = TextInput(
        label="Goal",
        required=False,
        style=TextStyle.short,
        placeholder="The goal of the game here (if you want a goal)...",
    )

    async def on_submit(self, interaction: Interaction):
        if not self.goal.value.isdigit():
            await interaction.response.send_message(
                "You have not typed in any numbers, moving on without a goal.",
                ephemeral=True,
            )
            value = None
        else:
            value = int(self.goal.value)

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

        self.view.goal = value

        await self.view.show_source(self.source.next(self.view), 1)


class StartModal(Modal):
    def __init__(self, source: Direction, view: CountingMenu) -> None:
        self.source = source
        self.view = view
        super().__init__(title="Start")

    start = TextInput(
        label="Start",
        required=True,
        style=TextStyle.short,
        placeholder="The start where the game begins from!",
    )

    async def on_submit(self, interaction: Interaction):
        if not self.start.value.isdigit():
            await interaction.response.send_message(
                "You have not typed in any numbers! Aborting.",
                ephemeral=True,
            )
            return

        if not int(self.start.value) > 0:
            await interaction.response.send_message(
                "Your start need to be greater than 0! Aborting.",
                ephemeral=True,
            )
            return

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

        self.view.start = int(self.start.value)
        await self.view.show_source(self.source.next(self.view), 1)


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
        super().__init__(
            ctx,
            items,
            title,
            None,
            description,
            True,
            10,
            label,
        )

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
    async def info(self) -> None:
        slash = await Slash(self.ctx.bot).__await__(
            self.ctx.bot.get_command("counting")
        )

        setup = self.ctx.bot.get_command("counting setup")
        cmd, setup = await slash.get_sub_command(setup)

        counting = self.ctx.bot.get_command("counting configure")
        cmd, configure = await slash.get_sub_command(counting)

        embed = ShakeEmbed()
        embed.title = Format.blockquotes(_("Welcome to „Counting“"))
        embed.set_author(
            name=_("Thanks for your interest about the game in this awesome place!"),
            icon_url=PartialEmoji(name="wumpus", id=1114674858706616422).url,
        )
        embed.description = "\n".join(
            Format.list(_)
            for _ in [
                _(
                    "The Counting Game is a fun and interactive game where "
                    "participants take turns posting numbers in ascending/descending order to a special text channel. "
                ),
                _(
                    "The purpose of the game is to continuously increase/decrease the number sequence by each player's contribution. "
                ),
                _(
                    "It can requires attention, coordination and quick action to maintain the flow and avoid mistakes. "
                    "The game encourages teamwork, healthy competition and interactive communication within the community. "
                ),
                _(
                    "It can be a fun challenge to see how high the number sequence can go as players work together to continue the counting game."
                ),
            ]
        )

        rules = [
            _("One person can't count numbers in a row (others are required)."),
            _("No botting, if you have failed to often, you'll get muted."),
            _("If you break the count, the count will reset to the start."),
        ]

        embed.add_field(
            name=_("The rules are simple"),
            value="\n".join(Format.list(_) for _ in rules),
            inline=False,
        )

        embed.add_field(
            name=_("How to setup the game?"),
            value=_(
                "Get started by using the command {command} to create and setup the essential channel"
            ).format(command=setup),
            inline=False,
        )
        embed.add_field(
            name=_("How to configure the game?"),
            value=_(
                "Customize all kind of properties for Counting by using the command {command}!"
            ).format(command=configure),
            inline=False,
        )
        embed.set_footer(
            text=_("The higher the number, the harder you fall!"),
            icon_url=self.bot.user.avatar.url,
        )

        embed.set_image(
            url="https://cdn.discordapp.com/attachments/946862628179939338/1060213944981143692/banner.png"
        )
        await self.ctx.chat(embed=embed, ephemeral=True)

    async def configure(
        self, channel: TextChannel, count: Optional[int], react: Optional[bool]
    ):
        async with self.ctx.db.acquire() as connection:
            query = "SELECT * FROM counting WHERE channel_id = $1"
            record = await connection.fetchrow(query, channel.id)
            if not record:
                await self.ctx.chat(
                    _(
                        "There is no Counting-Game in the given channel {channel} that we could configure."
                    ).format(channel=channel.mention)
                )
                return False

            count = (count - 1) if count else record["count"]
            react = react if not react is None else record["react"]
            query = 'UPDATE counting SET count = $2, "react" = $3 WHERE channel_id = $1'
            await connection.execute(query, channel.id, count, react)

        if count is not None:
            await channel.send(
                _("The next number in here has been set to {count}").format(count=count)
            )

        return await self.ctx.chat(
            _(
                "The stats of the Counting-Game in {channel} has been successfully configured."
            ).format(channel=channel.mention)
        )

    async def score(self, type: str) -> None:
        await self.ctx.defer()
        try:
            type = UserGuild[type.lower()].value
        except KeyError:
            type = Guild

        is_guild = type == Guild
        async with self.bot.gpool.acquire() as connection:
            if is_guild:
                query = "SELECT guild_id, count FROM counting;"
            else:
                query = "SELECT user_id, SUM(CASE WHEN failed = false THEN 1 ELSE -1 END) AS count FROM countings GROUP BY user_id;"
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

    async def setup(self, *args, **kwargs):
        menu = CountingMenu(ctx=self.ctx)
        message = await menu.setup(menu.sites)
        await menu.wait()

        embed = ShakeEmbed(timestamp=None)

        start = menu.start
        direction = menu.direction
        channel = menu.channel
        goal = menu.goal
        numbers = menu.numbers
        math = menu.math
        react = menu.react
        message_type = menu.message_type

        if menu.timeouted or any(
            _ is MISSING
            for _ in (direction, channel, start, goal, math, numbers, react)
        ):
            return

        if channel is None:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="counting", slowmode_delay=5
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

        if message_type == MessageTypes.webhook.value:
            try:
                webhook = await channel.create_webhook(
                    name=self.bot.user.name, avatar=None
                )
            except (HTTPException, Forbidden):
                embed = embed.to_error(
                    self.ctx,
                    description=_(
                        "I could not create a webhook in the TextChannel! Aborting..."
                    ),
                )
                await message.edit(embed=embed, view=None)
                return False
        else:
            webhook = None

        async with self.ctx.db.acquire() as connection:
            query = "SELECT * FROM counting WHERE channel_id = $1"
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

            query = """
                INSERT INTO counting 
                (channel_id, guild_id, goal, direction, webhook, count, start, numbers, math, react) 
                VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8, $9) 
                ON CONFLICT DO NOTHING"""

            await connection.execute(
                query,
                channel.id,
                self.ctx.guild.id,
                goal,
                direction,
                webhook.url if webhook else None,
                0 if direction else start + 1,
                numbers,
                math,
                react,
            )

        embed = embed.to_success(
            ctx=self.ctx,
            description=_("{game} is successfully set up in {channel}!").format(
                game="Counting", channel=channel.mention
            ),
        )
        embed.set_footer(text=_("Note: You can freely edit the text channel now."))

        await message.edit(
            embed=embed,
            view=None,
        )


#
############
