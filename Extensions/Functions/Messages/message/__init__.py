############
#
from importlib import reload
from typing import Dict

from asyncpg.exceptions import PostgresConnectionError
from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import AboveMeBatch, CountingBatch, OneWordBatch, ShakeBot, Testing

from . import message as _message
from . import testing


########
#
class on_message(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bot.cache.setdefault("Counting", dict())
        self.bot.cache.setdefault("AboveMe", dict())
        self.bot.cache.setdefault("OneWord", dict())

        try:
            reload(_message)
        except:
            pass

        for func in (self.counting, self.aboveme, self.oneword):
            func.add_exception_type(PostgresConnectionError)
            func.start()

    async def cog_unload(self):
        for func in (self.counting, self.aboveme, self.oneword):
            await func()
            func.stop()

    @loop(seconds=60.0)
    async def counting(self):
        query = """UPDATE counting set user_id = x.user_id, count = x.count, streak = x.streak, used = x.used, best = x.best, goal = x.goal 
                   FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, count BIGINT, user_id BIGINT, streak BIGINT, best BIGINT, goal BIGINT, react BOOLEAN, used TIMESTAMP, number BOOLEAN) 
                   WHERE counting.channel_id = x.channel_id;
                """
        CountingBatches: Dict[int, CountingBatch] = self.bot.cache["Counting"]
        if bool(CountingBatches):
            await self.bot.gpool.execute(query, list(CountingBatches.values()))
            self.bot.cache["Counting"].clear()

    @loop(seconds=60.0)
    async def aboveme(self):
        query = """UPDATE aboveme set user_id = x.user_id, count = x.count, phrases = x.phrases, used = x.used
                   FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, phrases TEXT[], react BOOLEAN, used TIMESTAMP) 
                   WHERE aboveme.channel_id = x.channel_id;
                """
        AboveMeBatches: Dict[int, AboveMeBatch] = self.bot.cache["AboveMe"]
        if bool(AboveMeBatches):
            await self.bot.gpool.execute(query, list(AboveMeBatches.values()))
            self.bot.cache["AboveMe"].clear()

    @loop(seconds=60.0)
    async def oneword(self):
        query = """UPDATE oneword set user_id = x.user_id, count = x.count, words = x.words, phrase = x.phrase, used = x.used
                   FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, words TEXT[], phrase TEXT, react BOOLEAN, used TIMESTAMP) 
                   WHERE oneword.channel_id = x.channel_id;
                """
        OneWordBatches: Dict[int, OneWordBatch] = self.bot.cache["OneWord"]
        if bool(OneWordBatches):
            await self.bot.gpool.execute(query, list(OneWordBatches.values()))
            self.bot.cache["OneWord"].clear()

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


async def setup(bot: ShakeBot):
    await bot.add_cog(on_message(bot))


#
############
