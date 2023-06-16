############
#
from importlib import reload
from typing import List, Tuple

from asyncpg.exceptions import PostgresConnectionError
from discord import PartialEmoji
from discord.ext.commands import Command, guild_only, hybrid_command
from discord.ext.tasks import loop

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..information import Information
from . import stats, testing


########
#
class stats_extension(Information):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(stats)
        except:
            pass
        self.fetch.add_exception_type(PostgresConnectionError)
        self.fetch.start()
        self.commands: List[Tuple[str, int]] = list()

    async def cog_unload(self):
        await self.fetch()
        self.fetch.stop()

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{CHART WITH UPWARDS TREND}")

    @loop(seconds=60.0)
    async def fetch(self) -> None:
        query = """SELECT command, COUNT(*) AS "uses" FROM commands GROUP BY command ORDER BY "uses" DESC;"""
        self.commands: List[Tuple[str, int]] = [
            (command, uses)
            for command, uses in await self.bot.pool.fetch(query)
            if not self.bot.get_command(command).extras.get("owner", False)
        ]

    @hybrid_command(name="stats", aliases=["s"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def stats(self, ctx: ShakeContext):
        _(
            """Get some basic information and statistics about me.
            
            very useful to stalk"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else stats

        try:
            await do.command(ctx=ctx, commands=self.commands).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(stats_extension(bot))


#
############
