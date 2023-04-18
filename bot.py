############
#
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import TYPE_CHECKING, Optional, Sequence
from asyncpg import Pool, Connection, connect, exceptions
from Classes.useful import source_lines
from logging import getLogger, Logger
from importlib import import_module
from discord.abc import Snowflake
from datetime import datetime
from discord import Message
from Classes.reddit import Reddit
from discord.ext.commands import Cog
from Classes.exceptions import CodeError
from Classes.helpful import BotBase, MISSING
from Classes.database.db import _kwargs, Table
from Classes.i18n import _, locale, current_locale

if TYPE_CHECKING:
    from Classes import __version__
else:
    __version__ = MISSING
########
#


class ShakeBot(BotBase):
    log: Logger
    scheduler: AsyncIOScheduler
    reloading: bool

    def __init__(self, **options):
        super().__init__(**options)
        self.log = getLogger(__name__)
        self.locales = self.pools = {}
        self.tests: dict[int, bool] = {}
        self.boot = datetime.now()
        self.lines = source_lines()
        self.scheduler = AsyncIOScheduler()
        self.locale = locale(self)
        self.reddit: Reddit = Reddit()
        self.__version__ = __version__
        

    async def setup_hook(self):
        self.emojis
        await super().setup_hook()
        await self.load_extensions()
        self.scheduler.start()

    async def process_commands(self, message: Message) -> None:
        await super().process_commands(message)
        self.config.reload()
        self.emojis.reload()
        return

    async def load_extensions(self):
        for extension in self.config.client.extensions:
            try: 
                await self.load_extension(extension)
            except ModuleNotFoundError as e:
                self.log.critical("Extension \"{}\" couldn\'t be loaded: {}".format(extension, e))
            except ImportError as e:
                self.log.critical("Extension \"{}\" couldn\'t be loaded {}".format(extension, e))
            except:
                await self.on_error('load_extensions')
        

    async def add_cog(self, cog: Cog, /, *, override: bool = False, guild: Optional[Snowflake] = MISSING, guilds: Sequence[Snowflake] = MISSING,) -> None:
        try:
            await super().add_cog(cog, override=override, guild=guild, guilds=guilds)
        except Exception as e:
            self.log.warn('"{}" couldn\'t get loaded: {}'.format(cog, e))
        return


    async def close(self) -> None:
        await super().close()
        if self.session:
            await self.session.close()
        self.log.info('Bot is shutting down')


    async def dump(self, content: str, lang: Optional[str] = 'txt'):
        async with self.session.post('https://hastebin.com/documents', data=content) as post:
            if post.status < 400: 
                return f'https://hastebin.com/{(await post.text())[8:-2]}'
        
        async with self.session.post("https://bin.readthedocs.fr/new", data={'code':content, 'lang': lang}) as post:
            if post.status < 400: 
                return post.url

        async with self.session.post('MYSTBIN_URLhttps://mystb.in/api/pastes', data=content) as post:
            if post.status < 400: 
                return 'https://mystb.in/' + (await post.json())['pastes'][0]['id']


    async def get_pool(self, _id) -> Pool:
        if not (guild := self.get_guild(_id)):
            return None
        try:
            locale = await self.locale.get_guild_locale(guild.id)
        except:
            locale = 'en-US'
        current_locale.set(locale)

        if (pool := self.pools.get(_id, None)):
            return pool
        connection: Connection = await connect(
            user=self.config.database.user, database=self.config.database.database, password=self.config.database.password, host='localhost'
        )
        try:
            await connection.execute(f'CREATE DATABASE "{_id}" OWNER "{self.config.database.user}"') 
        except:
            pass
        finally:
            import_module('Classes.database.#main') 
            self.pools[_id] = await Table.create_pool(self.config.database.postgresql+str(_id), **_kwargs)
            try:
                for table in Table.all_tables():
                    await table.create(item=str(_id), verbose=False, run_migrations=False)
            except exceptions.UniqueViolationError:
                pass
            await connection.close()
            return self.pools[_id]
#
############