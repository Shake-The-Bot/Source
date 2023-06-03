############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji, TextChannel
from discord.ext.commands import guild_only, hybrid_group

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..functions import Functions
from . import counting, testing


########
#
class counting_extension(Functions):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(counting)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{SQUARED UP WITH EXCLAMATION MARK}")

    @hybrid_group(name="counting")
    @guild_only()
    @setlocale()
    @locale_doc
    async def counting(self, ctx: ShakeContext):
        ...

    @counting.command(name="setup")
    @guild_only()
    @setlocale()
    @locale_doc
    async def setup(
        self,
        ctx: ShakeContext,
        /,
        channel: Optional[TextChannel] = None,
        goal: Optional[int] = None,
        hardcore: Optional[bool] = False,
        only_numbers: Optional[bool] = True,
    ):
        _(
            """Setup the whole counting game in seconds
            Get more information about the counting game with {command}"""
        ).format(command="`/counting info`")

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else counting

        try:
            await do.command(
                ctx=ctx,
                channel=channel,
                goal=goal,
                hardcore=hardcore,
                only_numbers=only_numbers,
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise

    @counting.command(name="info")
    @guild_only()
    @setlocale()
    @locale_doc
    async def info(self, ctx: ShakeContext):
        _("""Get the main information you need about the Counting-Game""")
        ...


async def setup(bot: ShakeBot):
    await bot.add_cog(counting_extension(bot))


#
############
