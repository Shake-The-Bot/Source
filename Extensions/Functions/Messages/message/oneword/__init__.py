############
#
from importlib import reload
from typing import Dict

from asyncpg.exceptions import PostgresConnectionError
from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import Batch, OneWordBatch, ShakeBot, Testing, current

from . import oneword as _message
from . import testing


########
#
class on_oneword(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

        self.bot.cache.setdefault("OneWord", dict())
        self.bot.cache.setdefault("OneWords", list())

        try:
            reload(_message)
        except:
            pass

        for func in (self.oneword, self.onewords):
            if not func.is_running():
                func.add_exception_type(PostgresConnectionError)
                func.start()

    async def cog_unload(self):
        for func in (self.oneword, self.onewords):
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
    async def oneword(self):
        batch: Dict[int, OneWordBatch] = self.bot.cache["OneWord"]
        if bool(batch):
            query = """UPDATE oneword set user_id = x.user_id, count = x.count, words = x.words, phrase = x.phrase, used = x.used, message_id = x.message_id
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, words TEXT[], phrase TEXT, message_id BIGINT, react BOOLEAN, used TIMESTAMP) 
                WHERE oneword.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["OneWord"].clear()

    @loop(seconds=15.0)
    async def onewords(self):
        batch: list[Batch] = self.bot.cache["OneWords"]
        if bool(batch):
            query = """INSERT INTO onewords (guild_id, channel_id, user_id, used, failed)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.failed
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, failed BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["OneWords"].clear()


async def setup(bot: ShakeBot):
    await bot.add_cog(on_oneword(bot))


#
############
