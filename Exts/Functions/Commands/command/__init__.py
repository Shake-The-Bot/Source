############
#
from importlib import reload
from typing import Optional, TypedDict

from asyncpg.exceptions import PostgresConnectionError
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import ShakeBot, ShakeContext, Testing

from . import command, testing

############
#


class DataBatchEntry(TypedDict):
    guild: Optional[int]
    channel: int
    author: int
    used: str
    prefix: str
    command: str
    failed: bool
    app_command: bool


class on_command(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bulk_insert.add_exception_type(PostgresConnectionError)
        self.bulk_insert.start()

    async def cog_unload(self):
        await self.api.session.close()
        self.bulk_insert.stop()

    @loop(seconds=10.0)
    async def bulk_insert(self):
        query = """INSERT INTO commands (guild_id, channel_id, author_id, used, prefix, command, failed, app_command)
                   SELECT x.guild, x.channel, x.author, x.used, x.prefix, x.command, x.failed, x.app_command
                   FROM jsonb_to_recordset($1::jsonb) AS
                   x(
                        guild BIGINT,
                        channel BIGINT,
                        author BIGINT,
                        used TIMESTAMP,
                        prefix TEXT,
                        command TEXT,
                        failed BOOLEAN,
                        app_command BOOLEAN
                    )
                """

        _data_batch: list[DataBatchEntry] = self.bot.cache["_data_batch"]
        if _data_batch:
            await self.bot.pool.execute(query, _data_batch)
            total = len(_data_batch)
            if total > 1:
                pass
                # self..info("Registered %s commands to the database.", total)
            self.bot.cache["_data_batch"].clear()

    @Cog.listener()
    async def on_command(self, ctx: ShakeContext):  # wurde nicht eingetragen
        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [ctx.author, ctx.guild, ctx.channel]
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                ctx.testing = False
        do = testing if test else command

        try:
            await do.Event(ctx=ctx, bot=self.bot).__await__()

        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_command(bot))


#
############
