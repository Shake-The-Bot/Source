from enum import Enum
from typing import Callable, List, Optional, Tuple

from discord import (
    Forbidden,
    HTTPException,
    Interaction,
    Message,
    PartialEmoji,
    SelectOption,
    TextChannel,
    ui,
)
from discord.utils import maybe_coroutine

from Classes import ShakeCommand, ShakeContext, ShakeEmbed, TextFormat, _


############
#
class Duration(Enum):
    forever = 0
    specific = 1
    until = 3


class Interval(Enum):
    never = 0
    daily = 1
    weekly = 7
    monthly = 31
    yearly = 356


class command(ShakeCommand):
    async def create(self):
        embed = ShakeEmbed()
        embed.description = TextFormat.bold(_("First step: Choose the repetition"))
        view = ScheduleView(cmd=self, ctx=self.ctx)
        view.message = await self.ctx.send(embed=embed, view=view)


class ScheduleView(ui.View):
    ctx: ShakeContext
    message: Message
    cmd: command

    def __init__(self, cmd, ctx):
        self.ctx = ctx
        self.cmd = cmd
        super().__init__()
        select = Select(
            options=[
                ("Never", "Just get reminded once", Interval.never.name),
                ("Daily", "Get reminded every day", Interval.daily.name),
                ("Weekly", "Get reminded every week", Interval.weekly.name),
                ("Monthly", "Get reminded every montg", Interval.monthly.name),
                ("Yearly", "Get reminded every year", Interval.yearly.name),
            ],
            placeholder="Choose the repetition...",
            function=self.interval,
        )
        self.item = select
        self.add_item(select)

    async def interval(self, interval: Interval):
        self._interval = Interval[interval]

        select = Select(
            options=[
                ("Forever", None, Duration.forever.name),
                ("Specific number of times", None, Duration.specific.name),
                ("Until", None, Duration.until.name),
            ],
            placeholder="Choose the repetition...",
            function=self.duration,
        )
        self.remove_item(self.item)
        self.item = select
        self.add_item(select)

        embed = ShakeEmbed()
        embed.description = TextFormat.bold(_("Second step: Choose the Duration"))

        await self.message.edit(embed=embed, view=self)

    async def duration(self, duration: Duration):
        self._duration = Duration[duration]
        await self.ctx.send(str(duration))


class Select(ui.Select):
    view: ScheduleView

    def __init__(
        self,
        options: List[Tuple[str, Optional[str], Enum]],
        placeholder: str,
        function: Callable,
    ):
        options = [
            SelectOption(label=label, description=description, value=value)
            for label, description, value in options
        ]
        super().__init__(placeholder=placeholder, options=options)
        self.function: Callable = function

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        return await maybe_coroutine(self.function, self.values[0])


#
############
