from enum import Enum
from typing import Optional, Union

from discord import ButtonStyle, ChannelType, Interaction, SelectOption, TextChannel
from discord.app_commands import AppCommandChannel
from discord.components import SelectOption, TextStyle
from discord.ui import Button, ChannelSelect, Modal, Select, TextInput
from discord.utils import MISSING

from Classes import MISSING, Format, ShakeCommand, ShakeEmbed, _
from Classes.accessoires import ForwardingFinishSource, ForwardingMenu, ForwardingSource
from Classes.helpful import ShakeContext, ShakeEmbed

############
#


class Intervals(Enum):
    never = 0
    daily = 1
    weekly = 7
    monthly = 31
    yearly = 365


class Durations(Enum):
    forever = 0
    specific = 1
    until = 3


class Types(Enum):
    webhook = 1
    message = 0


class SchedulerMenu(ForwardingMenu):
    interval: Intervals = MISSING
    duration: Durations = MISSING
    channel: Optional[TextChannel] = MISSING
    time: str = MISSING
    date: str = MISSING

    def __init__(self, ctx):
        super().__init__(ctx)
        self.finish = ForwardingFinishSource(self)
        self.finish.previous = Channel

        self.sites = [
            Interval(self),
            Duration(self),
            Channel(self),
            self.finish,
        ]


class Interval(ForwardingSource):
    view: SchedulerMenu
    item = Select(
        placeholder="Choose the repetition...",
        options=[
            SelectOption(label=label, description=description, value=value)
            for label, description, value in [
                ("Once", "Set the Alert for only once", Intervals.never.name),
                ("Daily", "Set the Alert for every day", Intervals.daily.name),
                ("Weekly", "Set the Alert for every week", Intervals.weekly.name),
                ("Monthly", "Set the Alert for every montg", Intervals.monthly.name),
                ("Yearly", "Set the Alert for every year", Intervals.yearly.name),
            ]
        ],
    )

    def __init__(self, view: SchedulerMenu) -> None:
        super().__init__(
            view=view,
            previous=None,
            next=Channel,
            items=[self.item, view.previous, view.cancel, view.next],
        )

    async def __call__(self, interaction: Interaction) -> None:
        value = (
            self.item.values[0]
            if bool(self.item.values)
            else None or self.view.interval
        )
        if value:  # select
            await self.callback(interaction, value)
        else:  # button
            return await interaction.response.send_message(
                "You have not selected a Interval", ephemeral=True
            )

    async def callback(self, interaction: Interaction, value: Intervals):
        self.view.interval = Intervals[value].value

        if self.view.interval != Intervals.never.value:
            self.next = Duration
        else:
            self.view.duration = None
        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            return await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()

        embed.title = _("Repetition")
        embed.description = Format.bold(
            _(
                "Decide to only get alerted once or choose the interval between the alerts!"
            )
        )

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class Duration(ForwardingSource):
    view: SchedulerMenu
    item = Select(
        placeholder="Choose the duration...",
        options=[
            SelectOption(label=label, description=description, value=value)
            for label, description, value in [
                ("Forever", None, Durations.forever.name),
                ("Specific number of times", None, Durations.specific.name),
                ("Until", None, Durations.until.name),
            ]
        ],
    )

    def __init__(self, view: SchedulerMenu) -> None:
        super().__init__(
            view=view,
            previous=Interval,
            next=Channel,
            items=[self.item, view.previous, view.cancel],
        )

    async def callback(self, interaction: Interaction, value: Durations):
        self.view.duration = Durations[value].value

        if self.view.duration == Durations.forever:
            ...
        elif self.view.duration == Durations.specific:
            ...
        else:  # until
            ...

        await self.view.show_source(source=self.next(self.view), rotation=1)
        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Scheduler duration"))
        interval = {i.value: i.name for i in Intervals}.get(self.view.interval)
        embed.title = Format.join(
            _("Decide for how long this interval should last"),
            "(" + interval.capitalize() + ")",
        )
        points = [
            _("You can have this scheduler to run for ever."),
            _("You can decide to run this scheduler for a specific number of times."),
            _("You can set a time where the scheduler should stop running."),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class Channel(ForwardingSource):
    view: SchedulerMenu
    channel: Optional[TextChannel]
    select = ChannelSelect(
        channel_types=[ChannelType.text], placeholder="Select a TextChannel!", row=1
    )
    button = Button(label=_("Use this one"), style=ButtonStyle.blurple, row=4)

    def __init__(self, view: SchedulerMenu) -> None:
        super().__init__(
            view=view,
            previous=Interval,
            next=MISSING,
            items=[self.select, view.previous, self.button, view.cancel],
        )

    async def __call__(self, interaction: Interaction) -> None:
        if bool(self.select.values):  # select
            value = self.select.values[0]
        else:  # button
            assert interaction.channel
            value = interaction.channel
        await self.callback(interaction, value)

    async def callback(
        self,
        interaction: Interaction,
        value: Union[Optional[AppCommandChannel], TextChannel] = None,
    ):
        if isinstance(value, AppCommandChannel):
            value = self.bot.get_channel(value.id)
        self.view.channel = value

        await interaction.response.send_modal(TimeModal(self, self.view))

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()

    def message(self) -> dict:
        embed = ShakeEmbed()
        embed.set_author(name=_("Scheduler channel"))
        embed.title = _("Choose in which text channel this reminder should be sent!")
        points = [
            _("You can set up an existing text channel from your server."),
            _("You can use this existing text channel."),
            _(
                "Alternatively, you have the option to have a new text channel created for it."
            ),
        ]
        embed.description = "\n".join(list(Format.list(_) for _ in points))

        embed.set_footer(
            text=_("You can come back here in the setup to change settings..")
        )
        return {"embed": embed}


class TimeModal(Modal):
    def __init__(self, source: Channel, view: SchedulerMenu) -> None:
        self.source = source
        self.view = view
        super().__init__(title="Goal")

    date = TextInput(
        label="Date",
        required=False,
        style=TextStyle.short,
        placeholder="The date for the scheduler",
    )

    time = TextInput(
        label="Time",
        required=False,
        style=TextStyle.short,
        placeholder="The time for the scheduler",
    )

    async def on_submit(self, interaction: Interaction):
        if not self.date and self.time:
            return await interaction.response.send_message(
                "You have not entered both time and date.",
                ephemeral=True,
            )

        self.view.date = self.date
        self.view.time = self.time

        await self.view.show_source(source=self.view.finish, rotation=1)

        if interaction and not interaction.response.is_done():
            await interaction.response.defer()


class command(ShakeCommand):
    async def create(self, *args, **kwargs):
        menu = SchedulerMenu(ctx=self.ctx)
        message = await menu.setup(menu.sites)
        await menu.wait()

        embed = ShakeEmbed(timestamp=None)

        duration = menu.duration
        channel = menu.channel
        interval = menu.interval

        if menu.timeouted:
            return

        if any(_ is MISSING for _ in (duration, channel, interval)):
            embed = embed.to_error(
                ctx=self.ctx, description=_("An error has occurred, try again later!")
            )
            return await message.edit(embed=embed, view=None)

        # async with self.ctx.db.acquire() as connection:
        #     query = "SELECT * FROM {game} WHERE channel_id = $1"
        #     for game in dbgames:
        #         record = await connection.fetchrow(query.format(game=game), channel.id)
        #         if record:
        #             embed = embed.to_error(
        #                 self.ctx,
        #                 description=_(
        #                     "There is already a game set up in {channel}. Aborting..."
        #                 ).format(channel=channel.mention),
        #             )
        #             await message.edit(embed=embed, view=None)
        #             return False

        #     query = """
        #         INSERT INTO counting
        #         (channel_id, guild_id, goal, direction, webhook, count, start, numbers, math, react)
        #         VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8, $9)
        #         ON CONFLICT DO NOTHING"""

        #     await connection.execute(
        #         query,
        #         channel.id,
        #         self.ctx.guild.id,
        #         goal,
        #         direction,
        #         webhook.url if webhook else None,
        #         0 if direction else start + 1,
        #         numbers,
        #         math,
        #         react,
        #     )

        embed = embed.to_success(
            ctx=self.ctx,
            description=_("The scheduler is successfully set up in {channel}!").format(
                channel=channel.mention
            ),
        )
        # embed.set_footer(
        #     text=_("Note: You can manage this servers schedulers with /schedulers.")
        # )

        await message.edit(
            embed=embed,
            view=None,
        )


#
############
