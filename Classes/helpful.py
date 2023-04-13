from __future__ import annotations
from importlib import import_module
from Classes.database.db import Table
from discord.player import AudioPlayer
from Classes.secrets.configuration import Config
from Classes.exceptions import ChannelNotFound
from asyncpg import Pool, connect, UndefinedTableError
from Exts.Functions.Debug.error import error
from discord.abc import T
from Classes.useful import MISSING
from aiohttp import ClientSession
from Classes.secrets.emojis import Emojis
from asyncio import TimeoutError
from traceback import print_exc
from contextlib import suppress
from inspect import signature
from datetime import datetime
from collections import deque
from logging import getLogger
from discord.ui import View
from Classes.i18n import _
from random import random
config = Config('config.toml')
emojis = Emojis('Assets/utils/emojis.toml')

from discord.ext.commands import (
    Context, AutoShardedBot, VoiceChannelConverter, Command, CommandNotFound, 
    CheckFailure, Context, CommandError, ChannelNotFound as _ChannelNotFound
)

from typing import (
    TYPE_CHECKING, Any, Awaitable, Callable, Tuple,
    Dict, Optional, Union, Sequence, Iterable
)
from discord import ( 
    HTTPException, AllowedMentions, Message, VoiceChannel, Message, AppInfo,
    User, Interaction, ClientException, FFmpegPCMAudio, ClientUser, utils, 
    Forbidden, File, GuildSticker, StickerItem, PartialMessage, TextChannel, 
    Thread, DMChannel, MessageReference, Embed, Colour, utils
)
embed_colour = config.embed.colour
embed_error_colour = config.embed.error_colour

if TYPE_CHECKING:
    from bot import ShakeBot
_kwargs = {'command_timeout': 60, 'max_size': 2, 'min_size': 1}
logger = getLogger(__name__)
########
#


"""    Migrations   """

class Migration():
    class dbitem():
        def __init__(self, i: str) -> None:
            self.valid: bool = True
            self.id = i
            is_config = i == 'config'
            is_bot = i == 'bot'
            if not is_bot and not is_config:
                if not i.isdigit():
                    self.valid = False
            self.name = '[' + i + ']' if is_config or is_bot else '[guild] ' + i

    def __init__(self, item: dbitem) -> None:
        self.item: Migration.dbitem = item
        self.__database_uri = config.database.postgresql + item.id
        self.is_config = item.name == 'config'
        self.is_bot = item.name == 'bot'
        self.is_guild = self.is_config == self.is_bot == False

    @property
    def name(self):
        return self.item.name
    
    @property
    def id(self):
        return self.item.id

    @property
    def database_uri(self):
        return self.__database_uri


    async def ensure_uri_can_run(self) -> bool:
        connection = await connect(config.database.postgresql)
        await connection.close()
        return True


    def import_module(self) -> str:
        return {'config': 'Classes.database.#config', 'bot': 'Classes.database.#bot'}.get(self.item.id, 'Classes.database.#main')


    async def get_table(self):
        await self.ensure_uri_can_run()
        try:
            pool = await Table.create_pool(config.database.postgresql + self.item.id, **_kwargs)
        except:
            await self.init()
            pool = await Table.create_pool(config.database.postgresql + self.item.id, **_kwargs)
        return pool


    async def init(self, reason: str = None):
        await self.ensure_uri_can_run()
        import_module(self.import_module())
        try:
            connection = await connect(config.database.postgresql)
            await connection.execute(f'CREATE DATABASE "{self.item.id}" OWNER "shake"')

            try: 
                pool = await Table.create_pool(config.database.postgresql + str(self.item.id), **_kwargs)

            except Exception:
                return print_exc()

        except:
            pool = await Table.create_pool(config.database.postgresql + self.item.id, **_kwargs)

        for table in Table.all_tables():
            try: 
                await table.create(item=self.item.id, verbose=False, run_migrations=False)

            except Exception as e:
                with suppress(Exception):
                    await connection.close()
                return False

        with suppress(Exception):
            await connection.close()
        return True


    async def migrate(self, reason: str = None):
        import_module(self.import_module())
            
        async def work(table: Table, invoked: bool = False):
            try:
                actually_migrated = table.write_migration(self.item.id)
            except RuntimeError as e:
                if not invoked:
                    await self.init()
                    work(table, invoked=True)
                return False
        
        for table in Table.all_tables():
            await work(table)
        return True


    async def upgrade(self, reason: str = None):
        pool = await self.get_table()
        import_module(self.import_module())

        async with pool.acquire() as con:
            tr = con.transaction()
            await tr.start()
            for table in Table.all_tables():
                try:
                    await table.migrate(item=self.item.id, index=-1, downgrade=False, verbose=True, connection=con)
                except RuntimeError:
                    await tr.rollback()
                    continue
            else:
                await tr.commit()
        return True


    async def downgrade(self, reason: str = None):
        pool = await self.get_table()
        import_module(self.import_module())

        async with pool.acquire() as con:
            tr = con.transaction()
            await tr.start()
            for table in Table.all_tables():
                try:
                    await table.migrate(item=self.item.id, index=-1, downgrade=True, verbose=True, connection=con)
                except RuntimeError:
                    await tr.rollback()
                    continue
            else:
                await tr.commit()
        return True


    async def drop(self, reason: str = None):
        pool = await self.get_table()
        import_module(self.import_module())
        async with pool.acquire() as connection:
            transaction = connection.transaction()
            await transaction.start()
            for table in Table.all_tables():
                try:
                    await table.drop(item=self.item.id, verbose=False, connection=connection)
                except UndefinedTableError:
                    continue
            else:
                await transaction.commit()
        return True


"""     Custom Context (Inherits from discord.ext.commands.Context)

For this function, I learned from two other programmers who inspired me on this.
https://github.com/Rapptz/RoboDanny & https://github.com/InterStella0/stella_bot
"""

class ShakeContext(Context):
    channel: Union[VoiceChannel, TextChannel, Thread, DMChannel]
    command: Command[Any, ..., Any]
    message: Message
    bot: ShakeBot
    pool: Pool

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.__dict__.update(dict.fromkeys(["waiting", "result", "channel_used", "running", "failed", "done"]))
        self.pool: Pool = self.bot.pools.get(self.guild.id, None)
        self.messages: Dict[int, Message] = {}
        self.reinvoked = False


    def reference(self) -> Optional[MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, Message):
            return ref.resolved.to_reference()
        return None


    @property
    def created_at(self) -> datetime:
        return self.message.created_at

    @property
    def db(self) -> Pool:
        return self.pool


    @property
    def session(self) -> ClientSession:
        return self.bot.session
    

    @property
    def session(self) -> ClientSession:
        return self.bot.session


    async def __await__(self, callback: Callable[..., Awaitable[Message]], /, **kwargs: Any) -> Message:
        error = kwargs.pop('error', False)
        if self.reinvoked and self.messages and not error:
            message = utils.find(
                lambda m: not getattr(m, "to_delete", False),
                reversed(self.messages.values()),
            )
            if message is not None:
                if "mention_author" in kwargs:
                    value = kwargs.pop("mention_author")
                    if kwargs.get("allowed_mentions", None) is None:
                        kwargs.update({"allowed_mentions": AllowedMentions(replied_user=value)})
                    else:
                        kwargs["allowed_mentions"].replied_user = value
                
                kwargs['attachments'] = []
                if file := kwargs.pop('file', None):
                    kwargs['attachments'].append(file)
                if files := kwargs.pop('files', None):
                    kwargs['attachments'] += files
                
                allowed_kwargs = list(signature(Message.edit).parameters)
                for key in list(kwargs):
                    if key not in allowed_kwargs:
                        kwargs.pop(key)
                kwargs.update({k: MISSING for k, v in kwargs.items() if v is None and k != 'delete_after'})
                return await message.edit(**kwargs)
        message = await callback(**kwargs)
        return message


    async def send(
        self, 
        content: Optional[str] = None,
        tts: bool = False,
        embed: Optional[ShakeEmbed] = None,
        error: bool = False,
        embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        suppress_embeds: bool = False,
        view: Optional[View] = None,
        ephemeral: bool = False,
        ) -> Message:
        if (not error) and (content == None) and (random() < (1 / 100)):
            content = '*'+_("Enjoying using Shake? I would love it if you </vote:1056920829620924439> for me or **share** me to your friends!").format(votelink=self.bot.config.other.vote)+'*'
        try:
            message = await self.__await__(super().send, 
                content=content, tts=tts, embed=embed, embeds=embeds, file=file, error=error,
                files=files, stickers=stickers, delete_after=delete_after, ephemeral=ephemeral,
                nonce=nonce, allowed_mentions=allowed_mentions, reference=reference or self.reference,
                mention_author=mention_author, suppress_embeds=suppress_embeds, view=view
            )
        except (Forbidden, HTTPException):
            return None
        else:
            return self.process(message)


    async def reply(
        self, content: Optional[str] = None, tts: bool = False,
        embed: Optional[ShakeEmbed] = None, embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None, files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None, nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None, mention_author: Optional[bool] = None,
        suppress_embeds: bool = False, view: Optional[View] = None, ephemeral: bool = False
    ) -> Message:
        try:
            message = await self.__await__(super().reply,
                content=content, tts=tts, embed=embed, embeds=embeds, file=file,
                files=files, stickers=stickers, delete_after=delete_after, ephemeral=ephemeral,
                nonce=nonce, allowed_mentions=allowed_mentions, view=view,
                mention_author=mention_author, suppress_embeds=suppress_embeds
            )
        except (Forbidden, HTTPException):
            return None
        else:
            return self.process(message)


    async def smart_reply(
        self, content: Optional[str] = None, tts: bool = False,
        embed: Optional[ShakeEmbed] = None, embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None, files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None, nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None, mention_author: Optional[bool] = False,
        suppress_embeds: bool = False, view: Optional[View] = None, ephemeral: bool = False
    ) -> Message:
        kwargs = {
            'content': content, 'embed': embed, 'embeds': embeds, 'file': file, 'suppress_embeds': suppress_embeds, 
            'stickers': stickers, 'delete_after': delete_after, 'ephemeral': ephemeral, 'nonce': nonce, 'files': files, 
            'allowed_mentions': allowed_mentions, 'view': view, 'mention_author': mention_author, 'tts': tts,
        }
        if ref := self.message.reference:
            kwargs['reference'] = ref
            if not mention_author:
                author = ref.cached_message.author
                kwargs['mention_author'] = (author in self.message.mentions and author.id not in self.message.raw_mentions)
            return await self.send(**kwargs)
        view = kwargs.pop('view', None)
        if getattr(self.channel, "last_message", MISSING) != self.message:
            return await self.reply(**kwargs)
        return await self.send(**kwargs)


    async def reinvoke(self, *, message: Optional[Message] = None, **kwargs: Any) -> None:
        self.reinvoked = True
        if message is None:
            return await super().reinvoke(**kwargs)
        if self.message != message:
            raise Exception("Context message and this message do not match.")
        new_ctx = await self.bot.get_context(message)
        for param in ['current_argument', 'current_parameter', 'message', 'running', 'invoked_with', 'prefix', 'command', 'args', 'view']:
            new_param = getattr(new_ctx, param)
            self.__dict__[param] = new_param
            setattr(self, param, new_param)
        await self.bot.invoke(self, typing=False)


    async def delete_all(self) -> None:
        if self.channel.permissions_for(self.me).manage_messages:
            await self.channel.delete_messages(self.messages.values())
        else:
            for message in self.messages.values():
                await message.delete(delay=0)
        self.messages.clear()

    def process(self, message: Message) -> Message:
        if message is not None:
            self.messages.update({message.id: message})
        return message

    def get_message(self, message_id: int) -> Optional[Message]:
        return self.messages.get(message_id)

    def pop_message(self, message_id: int) -> Optional[Message]:
        return self.messages.pop(message_id, None)


class BotBase(AutoShardedBot):

    user: ClientUser
    pools: Dict[int, Pool]
    gateway_handler: Any
    command_running = {}
    session: ClientSession
    bot_app_info: AppInfo
    _config: Config
    _emojis: Emojis

    
    def __init__(self, **options):
        owner_ids = options.pop("owner_ids")
        self.shake_id, *_ = owner_ids
        owner_ids=set(owner_ids)
        super().__init__(**options)
        self.cached_context = deque(maxlen=100)
        self.cached_posts: Dict[int, deque(maxlen=1000)] = {}
        self._session = None
        self._config = config
        self._emojis = emojis
    
    @property
    def session(self) -> ClientSession:
        return self._session

    @property
    def emojis(self) -> Emojis:
        return self._emojis
    
    @property
    def config(self) -> Config:
        return self._config

    @property
    def shake(self) -> Optional[User]:
        """Returns the owner as a discord.User Object """
        return self.get_user_global(self.shake_id)

    async def get_user_global(self, user_id: int) -> Optional[User]:
        """Returns/Retrieves a :class:`~discord.User` based on the given ID.
        You do not have to share any guilds with the user to get this information"""
        if not user_id or not isinstance(user_id, int):
            return None
        if user := (self.get_user(user_id) or await self.fetch_user(user_id)):
            return user
        return None

    async def close(self) -> None:
        for pool in self.pools.values():
            try:
                await pool.release()
            except:
                pass
            finally:
                await pool.close()

    async def running_command(self, ctx: ShakeContext, typing: bool = True, **flags):
        dispatch = flags.pop('dispatch', True)
        self.cached_context.append(ctx)
        if dispatch:
            self.dispatch('command', ctx)
        try:
            check = await self.can_run(ctx, call_once=flags.pop('call_once', True))
            if check or not flags.pop('call_check', True):
                ctx.running = True
                if typing:
                    await ctx.typing()
                await ctx.command.invoke(ctx)
            else:
                raise CheckFailure('The global check failed once.')
        except CommandError as exc:
            if dispatch:
                await ctx.command.dispatch_error(ctx, exc)
            if flags.pop('redirect_error', False):
                raise
        else:
            if dispatch:
                self.dispatch('command_completion', ctx)


    async def invoke(self, ctx: ShakeContext, typing: bool = True, **flags) -> None:
        dispatch = flags.get('dispatch', True)
        if ctx.command is not None:
            run_in_task = flags.pop('in_task', True)
            if run_in_task:
                command_task = self.loop.create_task(
                    self.running_command(ctx, typing=typing, **flags)
                )
                self.command_running.update({ctx.message.id: command_task})
            else:
                await self.running_command(ctx, typing=typing, **flags)
        elif ctx.invoked_with:
            exc = CommandNotFound()
            if dispatch:
                self.dispatch('command_error', ctx, exc)
            if flags.pop('redirect_error', False):
                raise exc


    async def get_context(self, message: Message, *, cls: Optional[Context] = ShakeContext) -> Union[ShakeContext, Context]:
        context = await super().get_context(message, cls=cls)
        return context
    

    async def process_commands(self, message: Message) -> None:
        if message.author.bot:
            return
        if not message.guild:
            return
        ctx: ShakeContext = await self.get_context(message)
        await self.invoke(ctx, typing=ctx.valid and not ctx.command.qualified_name in ('clear', 'dispatch'))

    
    async def setup_hook(self):
        self._session = ClientSession()
    
    async def on_error(self, event, *args, **kwargs):
        await error(bot=self, event=event).__await__()

    async def close(self) -> None:
        await super().close()

    @staticmethod
    async def on_connect():
        getLogger(__name__).info("Connection to Discord established.")

    @staticmethod
    async def on_disconnect():
        getLogger(__name__).info("Connection to Discord lost.")
    
    async def open(self, token: str,) -> None:
        try: 
            await super().start(token, reconnect=True)
        except Exception as error:
            self.log.error(error)


class ShakeEmbed(Embed):
    """"""
    def __init__(self, colour: Union[Colour, int] = embed_colour, timestamp: Optional[datetime] = None,
                 fields: Iterable[Tuple[str, str]] = (), field_inline: bool = False, **kwargs: Any):
        super().__init__(colour=colour, timestamp=timestamp or utils.utcnow(), **kwargs)
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)

    @classmethod
    def default(cls, ctx: Union[ShakeContext, Interaction], **kwargs: Any) -> ShakeEmbed:
        instance = cls(**kwargs)
        instance.timestamp = ctx.created_at
        author = getattr(ctx, 'author', str(MISSING)) if isinstance(ctx, (ShakeContext, Context)) else getattr(ctx, 'user', str(MISSING))
        bot = getattr(ctx, 'bot', str(MISSING)) if isinstance(ctx, (ShakeContext, Context)) else getattr(ctx, 'client', str(MISSING))
        instance.set_footer(text=f"Requested by {author} • via Shake", icon_url=bot.user.avatar.url)
        #instance.add_field(name='\u200b', value=bot.config.embed.footer.format(author), inline=False)
        return instance
    
    @classmethod
    def to_success(cls, *, message: str, colour: Union[Colour, int] = embed_colour, **kwargs: Any) -> ShakeEmbed:
        instance = cls(colour=colour, **kwargs)
        instance.timestamp = None
        return instance

    @classmethod
    def to_error(cls, colour: Union[Colour, int] = embed_error_colour, **kwargs: Any) -> ShakeEmbed:
        instance = cls(colour=colour, **kwargs)
        instance.timestamp = None
        return instance


class Voice:
    '''
    A class representing functions with Voice
    '''
    def __init__(
            self, 
            ctx: ShakeContext, 
            channel: VoiceChannel
        ):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot  = ctx.bot
        self._channel: VoiceChannel = channel
        self._player: Optional[AudioPlayer] = None

    async def __await__(self, channel: Optional[VoiceChannel] = MISSING):
        try:
            channel = await VoiceChannelConverter().convert(self.ctx, channel or self._channel)
        except _ChannelNotFound:
            raise ChannelNotFound(_("I could not find the given VoiceChannel "))
        else:
            self._channel = channel
        finally:
            return self.channel

    @property
    def volume(self):
        return self._volume
    
    @property
    def channel(self):
        return self._channel

    async def set_volume(self, volume):
        if not self.player:
            return
        

    async def set_channel(self, channel):
        channel = await self.__await__(channel)
        await self.cancel()

    async def connect(self, channel: Optional[VoiceChannel] = MISSING, **kwargs) -> T:
        try:
            voice = await (channel or self._channel).connect(reconnect=True, self_deaf=True, **kwargs)
        except ClientException:
            pass
        except TimeoutError:
            pass
        else:
            self._voice = voice
        finally:
            return self._voice


    async def play(self, filepath, volume):
        self.filepath = filepath
        self.volume = volume
        
        self._voice = await self._channel.connect(reconnect=True, self_deaf=True)

        if self._voice.is_playing():
            self._voice.stop()


        self._voice.play(source=FFmpegPCMAudio(filepath))
        self._player = self._voice._player

        # Wait until the sound clip is finished before leaving
        while self._player.is_playing():
            pass
        await self._voice.disconnect()


#
############