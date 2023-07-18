from collections import deque
from enum import Enum
from typing import Any, Coroutine, List, Optional, Union

from discord import ButtonStyle, Interaction, Message, PartialEmoji, SelectOption, ui
from discord.ui import Button, Item, Select
from discord.utils import maybe_coroutine

from Classes import Format, ShakeBot, ShakeCommand, ShakeContext, ShakeEmbed, _
from Classes.accessoires import ForwardingMenu, ForwardingSource

previousemoji = PartialEmoji(name="left", id=1033551843210579988)


############
#
class Types(Enum):
    webhook = 1
    message = 0


class Methods(Enum):
    sleep = 0
    database = 1
    scheduler = 2


class Durations(Enum):
    forever = 0
    specific = 1
    until = 3


class Intervals(Enum):
    never = 0
    daily = 1
    weekly = 7
    monthly = 31
    yearly = 365


class ScheduleMenu(ForwardingMenu):
    ctx: ShakeContext
    message: Message

    interval = Select(
        placeholder="Choose the repetition...",
        options=[
            SelectOption(label=label, description=description, value=value)
            for label, description, value in [
                ("Never", "Set the Alert for only once", Intervals.never.name),
                ("Daily", "Set the Alert for every day", Intervals.daily.name),
                ("Weekly", "Set the Alert for every week", Intervals.weekly.name),
                ("Monthly", "Set the Alert for every montg", Intervals.monthly.name),
                ("Yearly", "Set the Alert for every year", Intervals.yearly.name),
            ]
        ],
    )

    duration = Select(
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

    type = Select(
        placeholder="Choose the alert message type...",
        options=[
            SelectOption(label=label, description=description, value=value)
            for label, description, value in [
                ("Bot message", "Let me send the Alert", Types.message.name),
                ("Webhook", "Let a Webhook send the Alert", Types.webhook.name),
            ]
        ],
    )

    def __init__(self, ctx):
        self.start = Interval()

        self.interval.callback = self.duration
        self.duration.callback = self.types
        self.type.callback = self.finish
        super().__init__(ctx)
        sites = [
            [self.inter, self.cancel],
            [self.dur, self.cancel],
            [self.typ, self.cancel],
        ]
        self.setup(sites)

    async def start(self, interaction: Interaction):
        embed = ShakeEmbed()
        embed.title = _("Repetition")
        embed.description = Format.bold(
            _(
                "Decide to only get alerted once or choose the interval between the alerts!"
            )
        )

        self.update(1)
        await self.message.edit(embed=embed, view=self)

        if not interaction.response.is_done():
            await interaction.response.defer()


class Interval(ForwardingSource):
    view: ScheduleMenu
    interval: Optional[Intervals]

    def __init__(self, view: ScheduleMenu, item) -> None:
        super().__init__(view=view, item=item)
        self.next = Duration
        self.previous = None

    async def function(self, interaction: Interaction, value: Intervals):
        self.interval = Intervals[value]

        # if self.interval != Intervals.never:
        #     """-> when it is clear how long the alarm will last"""
        #     if self.time.small:
        #         self.view.method = Methods.sleep
        #     else:
        #         self.method = Methods.scheduler

        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.view.show_source(self.next())

    async def message(self) -> dict:
        embed = ShakeEmbed()
        embed.title = _("Repetition")
        embed.description = Format.bold(
            _(
                "Decide to only get alerted once or choose the interval between the alerts!"
            )
        )
        return {"embed": embed}


class Duration(ForwardingSource):
    view: ScheduleMenu
    duration: Optional[Durations]

    def __init__(self, view: ScheduleMenu, item) -> None:
        super().__init__(view=view, item=item)
        self.previous = Interval
        self.next = Type

    async def function(self, interaction: Interaction, value: Durations):
        self.duration = Durations[value]
        await interaction.response.defer()  ## send modal for timezone

        if self._duration == Durations.until:
            # self.view.insert()
            pass

        elif self._duration == Durations.specific:
            # self.view.insert()
            pass

        if not interaction.response.is_done():
            await interaction.response.defer()

        await self.view.show_source(self.next())

    async def message(self) -> dict:
        embed = ShakeEmbed()
        embed.description = Format.bold(_("Second step: Choose the duration"))
        return {"embed": embed}


class Type(ForwardingSource):
    view: ScheduleMenu
    type: Optional[Types]

    def __init__(self, view: ScheduleMenu, item) -> None:
        super().__init__(view=view, item=item)
        self.previous = Duration
        self.next = None

    async def function(self, interaction: Interaction, value: Types):
        self.type = Types[value]

        if not interaction.response.is_done():
            await interaction.response.defer()

        self.view.stop()
        # await self.view.show_next_page(self.next())

    async def message(self) -> dict:
        embed = ShakeEmbed()
        embed.description = Format.bold(_("Third step: Choose the Message Type"))
        return {"embed": embed}


class UntilModal:
    ...


class SpecificModal:
    ...


class command(ShakeCommand):
    """"""

    async def create(self):
        embed = ShakeEmbed(
            description=Format.bold(
                _("Before continuing you must click on the Setup button.")
            )
        )
        menu = ScheduleMenu(ctx=self.ctx)
        menu.setup()
        message = await menu.send(embed=embed)
        await menu.wait()


#
############
