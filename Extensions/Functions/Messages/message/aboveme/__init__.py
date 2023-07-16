############
#
from importlib import reload
from typing import Dict

from asyncpg.exceptions import PostgresConnectionError
from discord import Message
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from Classes import AboveMeBatch, AboveMesBatch, ShakeBot, Testing, current

from . import aboveme as _message
from . import testing


########
#
class on_aboveme(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

        self.bot.cache.setdefault("AboveMe", dict())
        self.bot.cache.setdefault("AboveMes", list())

        try:
            reload(_message)
        except:
            pass

        for func in (self.aboveme, self.abovemes):
            if not func.is_running():
                func.add_exception_type(PostgresConnectionError)
                func.start()

    async def cog_unload(self):
        for func in (self.aboveme, self.abovemes):
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
    async def aboveme(self):
        batch: Dict[int, AboveMeBatch] = self.bot.cache["AboveMe"]
        if bool(batch):
            query = """UPDATE aboveme set user_id = x.user_id, count = x.count, phrases = x.phrases, used = x.used, message_id = x.message_id
                FROM jsonb_to_recordset($1::jsonb) AS x(channel_id BIGINT, user_id BIGINT, count BIGINT, phrases TEXT[], message_id BIGINT, "react" BOOLEAN, used TIMESTAMP) 
                WHERE aboveme.channel_id = x.channel_id;
            """
            await self.bot.gpool.execute(query, list(batch.values()))
            self.bot.cache["AboveMe"].clear()

    @loop(seconds=15.0)
    async def abovemes(self):
        batch: list[AboveMesBatch] = self.bot.cache["AboveMes"]
        if bool(batch):
            query = """INSERT INTO abovemes (guild_id, channel_id, user_id, used, phrase, failed)
                SELECT x.guild_id, x.channel_id, x.user_id, x.used, x.phrase, x.failed
                FROM jsonb_to_recordset($1::jsonb) AS x(guild_id BIGINT, channel_id BIGINT, user_id BIGINT, used TIMESTAMP, phrase TEXT, failed BOOLEAN)
            """
            await self.bot.gpool.execute(query, batch)
            self.bot.cache["AboveMes"].clear()


async def setup(bot: ShakeBot):
    await bot.add_cog(on_aboveme(bot))


#
############
