############
#
from importlib import reload
from typing import Dict

from asyncpg.exceptions import PostgresConnectionError
from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import (
    AboveMeBatch,
    AboveMesBatch,
    CountingBatch,
    FunctionsBatch,
    OneWordBatch,
    ShakeBot,
    Testing,
)

from . import message as _message
from . import testing


########
#
class on_message(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

        for name in ("Counting", "AboveMe", "OneWord"):
            self.bot.cache.setdefault(name, dict())
        for name in ("Countings", "AboveMes", "OneWords"):
            self.bot.cache.setdefault(name, list())

        try:
            reload(_message)
        except:
            pass

        for func in (self.counting, self.aboveme, self.oneword):
            if not func.is_running():
                func.add_exception_type(PostgresConnectionError)
                func.start()

    async def cog_unload(self):
        for func in (self.counting, self.aboveme, self.oneword):
            await func()
            func.stop()

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [message.channel, message.guild, message.author]
        )
        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                test = False
        do = testing if test else _message

        try:
            await do.Event(message=message, bot=self.bot).__await__()

        except:
            if test:
                raise Testing
            raise

    @loop(seconds=30.0)
    async def counting(self):
        batch: Dict[int, CountingBatch] = self.bot.cache["Counting"]
        if bool(batch):
            query = """UPDATE counting set user_id = x.user_id, count = x.count, streak = x.streak, used = x.used, best = x.best, goal = x.goal 
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, count BIGINT, user_id BIGINT, streak BIGINT, best BIGINT, goal BIGINT, "react" BOOLEAN, used TIMESTAMP, numbers BOOLEAN) 
                WHERE counting.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["Counting"].clear()

        batch: list[FunctionsBatch] = self.bot.cache["Countings"]
        if bool(batch):
            query = """INSERT INTO countings (guild_id, channel_id, user_id, used, count, failed)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.count, x.failed
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, count BIGINT, failed BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["Countings"].clear()

    @loop(seconds=60.0)
    async def aboveme(self):
        batch: Dict[int, AboveMeBatch] = self.bot.cache["AboveMe"]
        if bool(batch):
            query = """UPDATE aboveme set user_id = x.user_id, count = x.count, phrases = x.phrases, used = x.used
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, phrases TEXT[], "react" BOOLEAN, used TIMESTAMP) 
                WHERE aboveme.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["AboveMe"].clear()

        batch: list[AboveMesBatch] = self.bot.cache["AboveMes"]
        if bool(batch):
            query = """INSERT INTO abovemes (guild_id, channel_id, user_id, used, phrase, failed)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.phrase, x.failed
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, phrase TEXT, failed BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["AboveMes"].clear()

    @loop(seconds=60.0)
    async def oneword(self):
        batch: Dict[int, OneWordBatch] = self.bot.cache["OneWord"]
        if bool(batch):
            query = """UPDATE oneword set user_id = x.user_id, count = x.count, words = x.words, phrase = x.phrase, used = x.used
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, words TEXT[], phrase TEXT, react BOOLEAN, used TIMESTAMP) 
                WHERE oneword.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["OneWord"].clear()

        batch: list[FunctionsBatch] = self.bot.cache["OneWords"]
        if bool(batch):
            query = """INSERT INTO onewords (guild_id, channel_id, user_id, used, count, failed)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.count, x.failed
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, count BIGINT, failed BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["OneWords"].clear()


async def setup(bot: ShakeBot):
    await bot.add_cog(on_message(bot))


#
############
