############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, has_permissions, hybrid_command, is_owner
from discord.ext.tasks import loop

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..community import Community
from . import testing as schedule


########
#
class schedule_extension(Community):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot, cog=self)
        try:
            reload(schedule)
        except:
            pass

    @loop(seconds=1)
    async def check(self):
        print(0)
        ...

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR NUMBERS}")

    @hybrid_command(name="schedule")
    @guild_only()
    @is_owner()
    @has_permissions(administrator=True)
    @extras(owner=True)
    @setlocale()
    @locale_doc
    async def schedule(self, ctx: ShakeContext):
        _(
            """Scheduled Events are Reminders, which you can let recurr on a chosen Interval. 
            With a set timezone, you can choose the Start Time and the Message with the corresponding TextChannel."""
        )

        if ctx.testing:
            try:
                reload(schedule)
            except Exception as e:
                await self.bot.testing_error(module=schedule, error=e)
                ctx.testing = False

        do = schedule

        try:
            await do.command(ctx=ctx).create()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(schedule_extension(bot))


#
############
