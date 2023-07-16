############
#
from importlib import reload
from typing import Dict, Tuple

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
        self.commands: Dict[Tuple[str, int]] = dict()

    async def cog_unload(self):
        await self.fetch()
        self.fetch.stop()

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{CHART WITH UPWARDS TREND}")

    @loop(seconds=60.0)
    async def fetch(self) -> None:
        self.commands.clear()

        query = """SELECT command, COUNT(*) AS "uses" FROM commands GROUP BY command ORDER BY "uses" DESC;"""

        for name, uses in await self.bot.pool.fetch(query):
            if not uses > 1:
                continue
            command = self.bot.get_command(name)
            if not command:
                continue
            extras = getattr(command.callback, "extras", None)
            if extras and (extras.get("owner", None) or extras.get("hidden", None)):
                continue
            self.commands[name] = uses

    @hybrid_command(name="stats", aliases=["about", "info", "botinfo", "bot"])
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
