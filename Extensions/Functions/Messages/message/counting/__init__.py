############
#
from importlib import reload
from typing import Dict

from asyncpg.exceptions import PostgresConnectionError
from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import CountingBatch, CountingsBatch, ShakeBot, Testing, current

from . import counting as _message
from . import testing


########
#
class on_counting(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

        self.bot.cache.setdefault("Counting", dict())
        self.bot.cache.setdefault("Countings", list())

        try:
            reload(_message)
        except:
            pass

        for func in (self.counting, self.countings):
            if not func.is_running():
                func.add_exception_type(PostgresConnectionError)
                func.start()

    async def cog_unload(self):
        for func in (self.counting, self.countings):
            await func()
            func.stop()

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        locale = await self.bot.i18n.get_user(message.author.id, default="en-US")
        current.set(locale)

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
            query = """UPDATE counting set user_id = x.user_id, count = x.count, streak = x.streak, used = x.used, best = x.best, message_id = x.message_id, done = x.done, webhook = x.webhook
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, count BIGINT, user_id BIGINT, streak BIGINT, best BIGINT, goal BIGINT, "react" BOOLEAN, used TIMESTAMP, math BOOLEAN, numbers BOOLEAN, direction BOOLEAN, start BIGINT, message_id BIGINT, done BOOLEAN, webhook TEXT) 
                WHERE counting.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["Counting"].clear()

    @loop(seconds=15.0)
    async def countings(self):
        batch: list[CountingsBatch] = self.bot.cache["Countings"]
        if bool(batch):
            query = """INSERT INTO countings (guild_id, channel_id, user_id, used, count, failed, direction)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.count, x.failed, x.direction
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, count BIGINT, failed BOOLEAN, direction BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["Countings"].clear()


async def setup(bot: ShakeBot):
    await bot.add_cog(on_counting(bot))


#
############
