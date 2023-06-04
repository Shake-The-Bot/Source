from __future__ import annotations

from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from inspect import signature
from json import dump, load
from os import replace
from pathlib import Path
from re import Match, compile, sub
from threading import Thread
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
)
from uuid import uuid4

from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import Connection, Pool
from discord import (
    AllowedMentions,
    AppInfo,
    ClientUser,
    Colour,
    DMChannel,
    Embed,
    File,
    Forbidden,
    GuildSticker,
    HTTPException,
    Interaction,
    Message,
    MessageReference,
    PartialMessage,
    StickerItem,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
    utils,
)
from discord.ext.commands import (
    AutoShardedBot,
    CheckFailure,
    Command,
    CommandError,
    CommandNotFound,
    Context,
)
from discord.ui import View

from Classes.i18n import Locale, _, mo
from Classes.tomls import Config, Emojis, config, emojis
from Classes.useful import (
    MISSING,
    DatabaseProtocol,
    ExpiringCache,
    FormatTypes,
    Ready,
    TextFormat,
    source_lines,
)
from Exts.Functions.Debug.error import error

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import ShakeContext, ShakeEmbed

else:
    from discord import Embed as ShakeEmbed
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext
p = ThreadPoolExecutor(2)
b = lambda t: TextFormat.format(t, type=FormatTypes.bold)
############
#

__all__ = (
    "BotBase",
    "ShakeContext",
    "ShakeEmbed",
    "Migration",
)


_kwargs = {"command_timeout": 60, "max_size": 2, "min_size": 1}
########
#


"""     Custom Context (Inherits from discord.ext.commands.Context)

For this function, I learned from two other programmers who inspired me on this.
https://github.com/Rapptz/RoboDanny & https://github.com/InterStella0/stella_bot"""


class ShakeContext(Context):
    channel: Union[VoiceChannel, TextChannel, Thread, DMChannel]
    command: Command[Any, ..., Any]
    message: Message
    testing: bool
    bot: "ShakeBot"
    pool: Pool

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.__dict__.update(
            dict.fromkeys(["waiting", "result", "running", "failed", "done"])
        )
        self.__testing = (
            True
            if any(
                _.id in set(self.bot.testing.keys())
                for _ in [self.author, self.guild, self.channel]
            )
            else False
        )
        if self.__testing and getattr(self.command, "name", None):
            tests: dict = self.bot.cache["tests"]
            tests[self.command] = self
        self.messages: Dict[int, Message] = dict()
        self.reinvoked: bool = False
        self.done: bool = False

    def reference(self) -> Optional[MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, Message):
            return ref.resolved.to_reference()
        return None

    @property
    def created_at(self) -> datetime:
        return self.message.created_at

    @property
    def db(self) -> DatabaseProtocol:
        return self.bot.gpool

    @property
    def testing(self) -> bool:
        return self.__testing

    @testing.setter
    def testing(self, value):
        self.__testing: bool = value

    @property
    def session(self) -> ClientSession:
        return self.bot.session

    async def __await__(
        self,
        callback: Callable[..., Awaitable[Message]],
        /,
        forced: Optional[bool] = False,
        **kwargs: Any,
    ) -> Message:
        if self.reinvoked and self.messages and not forced:
            message: Optional[Message] = utils.find(
                lambda m: not getattr(m, "to_delete", False),
                reversed(self.messages.values()),
            )
            if message is not None:
                if "mention_author" in kwargs:
                    value = kwargs.pop("mention_author")
                    if kwargs.get("allowed_mentions", None) is None:
                        kwargs.update(
                            {"allowed_mentions": AllowedMentions(replied_user=value)}
                        )
                    else:
                        kwargs["allowed_mentions"].replied_user = value

                kwargs["attachments"] = []
                if file := kwargs.pop("file", None):
                    kwargs["attachments"].append(file)
                if files := kwargs.pop("files", None):
                    kwargs["attachments"] += files

                allowed_kwargs = set(signature(Message.edit).parameters)
                for key in set(kwargs):
                    if key not in allowed_kwargs:
                        kwargs.pop(key)
                kwargs = {k: v for k, v in kwargs.items() if v != None}
                return await message.edit(**kwargs)
        message = await callback(**kwargs)
        return message

    @utils.copy_doc(Context.send)
    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[Embed] = None,
        embeds: Optional[Sequence[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = False,
        view: Optional[View] = None,
        suppress_embeds: bool = False,
        ephemeral: bool = False,
        silent: bool = False,
        forced: Optional[bool] = False,
    ) -> Message:
        try:
            message = await self.__await__(
                super().send,
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                file=file,
                forced=forced,
                files=files,
                stickers=stickers,
                delete_after=delete_after,
                ephemeral=ephemeral,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                reference=reference or self.reference(),
                mention_author=mention_author,
                suppress_embeds=suppress_embeds,
                view=view,
                silent=silent,
            )
        except (Forbidden, HTTPException):
            return None
        else:
            return self.process(message)

    @utils.copy_doc(Context.reply)
    async def reply(
        self,
        content: Optional[str] = None,
        tts: bool = False,
        embed: Optional[ShakeEmbed] = None,
        embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = False,
        suppress_embeds: bool = False,
        view: Optional[View] = None,
        ephemeral: bool = False,
        forced: Optional[bool] = False,
    ) -> Message:
        try:
            message = await self.__await__(
                super().reply,
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                file=file,
                forced=forced,
                files=files,
                stickers=stickers,
                delete_after=delete_after,
                ephemeral=ephemeral,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                view=view,
                mention_author=mention_author,
                suppress_embeds=suppress_embeds,
            )
        except (Forbidden, HTTPException):
            return None
        else:
            return self.process(message)

    async def smart_reply(
        self,
        content: Optional[str] = None,
        tts: bool = False,
        embed: Optional[ShakeEmbed] = None,
        embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = False,
        suppress_embeds: bool = False,
        view: Optional[View] = None,
        ephemeral: bool = False,
        forced: Optional[bool] = False,
    ) -> Message:
        kwargs = {
            "content": content,
            "embed": embed,
            "embeds": embeds,
            "file": file,
            "suppress_embeds": suppress_embeds,
            "stickers": stickers,
            "delete_after": delete_after,
            "ephemeral": ephemeral,
            "nonce": nonce,
            "files": files,
            "allowed_mentions": allowed_mentions,
            "view": view,
            "mention_author": mention_author,
            "tts": tts,
            "forced": forced,
        }
        if ref := self.message.reference:
            kwargs["reference"] = ref
            if not mention_author:
                author = ref.cached_message.author
                kwargs["mention_author"] = (
                    author in self.message.mentions
                    and author.id not in self.message.raw_mentions
                )
            return await self.send(**kwargs)
        if getattr(self.channel, "last_message", MISSING) not in [
            self.message,
            MISSING,
        ]:
            return await self.reply(**kwargs)
        return await self.send(**kwargs)

    async def reinvoke(
        self, *, message: Optional[Message] = None, **kwargs: Any
    ) -> None:
        self.reinvoked = True
        if message is None:
            return await super().reinvoke(**kwargs)
        if self.message != message:
            raise Exception("Context message and this message do not match.")
        new_ctx = await self.bot.get_context(message)
        for param in [
            "current_argument",
            "current_parameter",
            "message",
            "running",
            "invoked_with",
            "prefix",
            "command",
            "args",
            "view",
        ]:
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

    def get(self, message_id: int) -> Optional[Message]:
        return self.messages.get(message_id)

    def pop(self, message_id: int) -> Optional[Message]:
        return self.messages.pop(message_id, None)


"""     Custom Bot (Inherits from discord.ext.commands.AutoSharedBot)
"""


class BotBase(AutoShardedBot):
    user: ClientUser
    boot: datetime
    gateway_handler: Any
    cache = dict()
    session: ClientSession
    bot_app_info: AppInfo
    _config: Config
    _emojis: Emojis

    def __init__(self, **options):
        owner_ids = options.pop("owner_ids")
        self.shake_id, *_ = owner_ids
        self.cache.setdefault("pages", dict())
        self.cache.setdefault("locales", dict())
        self.cache.setdefault("_data_batch", list())
        self.cache.setdefault("testing", {1036952232719024129: None})
        self.cache.setdefault("context", deque(maxlen=100))
        self.cache.setdefault("tests", ExpiringCache(60 * 5))
        self.cache.setdefault("cached_posts", dict())
        self._session = None
        self._config = config
        self._emojis = emojis
        super().__init__(**options)
        self.ready_shards: "Ready" = Ready(sequence=range(self.shard_count))

    @property
    def session(self) -> ClientSession:
        return self._session

    @property
    def testing(self) -> Dict[int, Any]:
        return self.cache["testing"]

    @property
    def emojis(self) -> Emojis:
        return self._emojis

    @property
    def config(self) -> Config:
        return self._config

    @property
    def shake(self) -> Optional[User]:
        """Returns the owner as a discord.User Object"""
        return self.get_user_global(self.shake_id)

    def get_emoji_local(self, dictionary: Any, name: str) -> Any:
        dictionary = getattr(self.emojis, dictionary, MISSING)
        if dictionary is MISSING:
            pass
            return None
        emoji = getattr(dictionary, name, MISSING)
        if emoji is MISSING:
            return None
        return emoji

    async def get_user_global(self, user_id: int) -> Optional[User]:
        """Returns/Retrieves a :class:`~discord.User` based on the given ID.
        You do not have to share any guilds with the user to get this information"""
        if not user_id or not isinstance(user_id, int):
            return None
        if user := (await self.fetch_user(user_id) or self.get_user(user_id)):
            return user
        return None

    async def running_command(self, ctx: ShakeContext, typing: bool = True, **flags):
        dispatch = flags.pop("dispatch", True)
        self.cache["context"].append(ctx)
        if dispatch:
            self.dispatch("command", ctx)
        try:
            check = await self.can_run(ctx, call_once=flags.pop("call_once", True))
            if check or not flags.pop("call_check", True):
                ctx.running = True
                if typing:
                    await ctx.typing()
                await ctx.command.invoke(ctx)
            else:
                raise CheckFailure("The global check failed once.")
        except CommandError as exc:
            if dispatch:
                await ctx.command.dispatch_error(ctx, exc)
            if flags.pop("redirect_error", False):
                raise
        else:
            if dispatch:
                self.dispatch("command_completion", ctx)

    async def invoke(self, ctx: ShakeContext, typing: bool = True, **flags) -> None:
        dispatch = flags.get("dispatch", True)
        if ctx.command is not None:
            if ctx.testing:
                self.cache["tests"][ctx.command] = ctx
            run_in_task = flags.pop("in_task", True)
            if run_in_task:
                command_task = self.loop.create_task(
                    self.running_command(ctx, typing=typing, **flags)
                )
                self.cache.setdefault("command_running", {}).update(
                    {ctx.message.id: command_task}
                )
            else:
                await self.running_command(ctx, typing=typing, **flags)
        elif ctx.invoked_with:
            exc = CommandNotFound()
            if dispatch:
                self.dispatch("command_error", ctx, exc)
            if flags.pop("redirect_error", False):
                raise exc

    async def get_context(
        self, message: Message, *, cls: Optional[Context] = ShakeContext
    ) -> Union[ShakeContext, Context]:
        context = await super().get_context(message, cls=cls)
        return context

    async def close(self):
        if hasattr(self, "scheduler") and self.scheduler.running:
            self.scheduler.shutdown()
        if self.session and not self.session.closed:
            await self.session.close()
        await super().close()

    async def load_extensions(self):
        for extension in self.config.client.extensions:
            try:
                await self.load_extension(extension)
            except ModuleNotFoundError as e:
                self.log.critical(
                    'Extension "{}" couldn\'t be loaded: {}'.format(extension, e)
                )
            except ImportError as e:
                self.log.critical(
                    'Extension "{}" couldn\'t be loaded {}'.format(extension, e)
                )
            except:
                await self.on_error("load_extensions")

    async def process_commands(self, message: Message) -> None:
        await self.wait_until_ready()
        if message.author.bot:
            return
        if not message.guild:
            return
        ctx: ShakeContext = await self.get_context(message)
        await self.invoke(
            ctx,
            typing=ctx.valid
            and not ctx.command.qualified_name in ["clear", "dispatch"],
        )

    async def setup_hook(self):
        self._session = ClientSession()
        self.locale: Locale = Locale(self)
        mo()
        self.lines: int = source_lines()
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        await self.load_extensions()
        self.scheduler.start()

    async def register_command(self, ctx: ShakeContext) -> None:
        if ctx.command is None:
            return

        self.cache["_data_batch"].append(
            {
                "guild": None if ctx.guild is None else ctx.guild.id,
                "channel": ctx.channel.id,
                "author": ctx.author.id,
                "used": ctx.message.created_at.isoformat(),
                "prefix": ctx.prefix,
                "command": ctx.command.qualified_name,
                "failed": ctx.command_failed,
                "app_command": ctx.interaction is not None,
            }
        )

    async def on_error(self, event, *args, **kwargs):
        await error(bot=self, event=event).__await__()

    async def start(self, token: str) -> None:
        try:
            await super().start(token, reconnect=True)
        except Exception as error:
            self.log.error(error)


class ShakeEmbed(Embed):
    """lazy"""

    def __init__(
        self,
        colour: Union[Colour, int] = MISSING,
        timestamp: Optional[datetime] = MISSING,
        fields: Iterable[Tuple[str, str]] = (),
        field_inline: bool = False,
        **kwargs: Any,
    ):
        super().__init__(
            colour=colour or config.embed.colour,
            timestamp=timestamp if not timestamp is MISSING else utils.utcnow(),
            **kwargs,
        )
        for n, v in fields:
            self.add_field(name=n, value=v, inline=field_inline)

    @classmethod
    def default(
        cls, ctx: Union[ShakeContext, Interaction], **kwargs: Any
    ) -> ShakeEmbed:
        instance = cls(**kwargs)
        instance.timestamp = ctx.created_at
        author = (
            getattr(ctx, "author", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "user", str(MISSING))
        )
        bot: "ShakeBot" = (
            getattr(ctx, "bot", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "client", str(MISSING))
        )
        instance.set_footer(
            text=f"Requested by {author} • via Shake", icon_url=bot.user.avatar.url
        )
        # instance.add_field(name='\u200b', value=bot.config.embed.footer.format(author), inline=False)
        return instance

    @classmethod
    def to_success(
        cls,
        ctx: Union[ShakeContext, Interaction],
        colour: Optional[Union[Colour, int]] = None,
        **kwargs: Any,
    ) -> ShakeEmbed:
        bot: "ShakeBot" = (
            getattr(ctx, "bot", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "client", str(MISSING))
        )
        if description := kwargs.pop("description", None):
            kwargs[
                "description"
            ] = f"{bot.emojis.hook} {bot.emojis.prefix} **{description}**"
        instance = cls(colour=colour or 0x00CC88, **kwargs)
        instance.timestamp = None
        return instance

    @classmethod
    def to_error(
        cls,
        ctx: Union[ShakeContext, Interaction],
        colour: Optional[Union[Colour, int]] = MISSING,
        **kwargs: Any,
    ) -> ShakeEmbed:
        colour = colour or 0xFF0000
        bot: "ShakeBot" = (
            getattr(ctx, "bot", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "client", str(MISSING))
        )
        if description := kwargs.pop("description", None):
            kwargs[
                "description"
            ] = f"{bot.emojis.cross} {bot.emojis.prefix} **{description}**"
        instance = cls(colour=colour, **kwargs)
        instance.timestamp = None
        return instance


class Revisions(TypedDict):
    # The version key represents the current activated version
    # So v1 means v1 is active and the next revision should be v2
    # In order for this to work the number has to be monotonically increasing
    # and have no gaps
    version: int
    base_url: str


REVISION_FILE = compile(
    r"(?P<kind>V|U)(?P<version>[0-9]+)_(?P<type>bot|guild)_(?P<description>.+).sql"
)


class Revision:
    __slots__ = ("kind", "version", "description", "file")

    def __init__(
        self, *, kind: str, version: int, description: str, file: Path
    ) -> None:
        self.kind: str = kind
        self.version: int = version
        self.description: str = description
        self.file: Path = file

    @classmethod
    def from_match(cls, match: Match[str], file: Path):
        return cls(
            kind=match.group("kind"),
            version=int(match.group("version")),
            description=match.group("description"),
            file=file,
        )


class Migration:
    def __init__(
        self,
        type: Literal["guild", "bot"],
        base_url: str = config.database.postgresql,
        *,
        filename: str = "Migrations/revisions.json",
    ):
        self.filename: str = filename
        self.base_url = base_url
        self.type: Literal["guild", "bot"] = type
        self.root: Path = Path(filename).parent
        self.revisions: dict[int, Revision] = self.get_revisions()
        self.load()

    def ensure_path(self) -> None:
        self.root.mkdir(exist_ok=True)

    def load_metadata(self) -> Revisions:
        try:
            with open(self.filename, "r", encoding="utf-8") as fp:
                return load(fp)
        except FileNotFoundError:
            return {
                "version": 0,
                "base_url": MISSING,
            }

    def get_revisions(self) -> dict[int, Revision]:
        result: dict[int, Revision] = {}
        for file in self.root.glob("*.sql"):
            match = REVISION_FILE.match(file.name)
            if match is not None:
                rev = Revision.from_match(match, file)
                result[rev.version] = rev

        return result

    def dump(self) -> Revisions:
        return {
            "version": self.version,
            "base_url": self.base_url,
        }

    def load(self) -> None:
        self.ensure_path()
        data = self.load_metadata()
        self.version: int = data["version"]
        self.using_uri: str = self.base_url + self.type

    def save(self):
        temp = f"{self.filename}.{uuid4()}.tmp"
        with open(temp, "w", encoding="utf-8") as tmp:
            dump(self.dump(), tmp)

        # atomically move the file
        replace(temp, self.filename)

    def is_next_revision_taken(self) -> bool:
        return self.version + 1 in self.revisions

    @property
    def ordered_revisions(self) -> list[Revision]:
        return sorted(self.revisions.values(), key=lambda r: r.version)

    def create_revision(self, reason: str, *, kind: str = "V") -> Revision:
        cleaned = sub(r"\s", "_", reason)
        sql = f"{kind}{self.version + 1}_{self.type}_{cleaned}.sql"
        path = self.root / sql

        stub = (
            f"-- Revises: V{self.version + 1}\n"
            f"-- Creation Date: {datetime.utcnow()} UTC\n"
            f"-- Reason: {reason}\n\n"
        )

        with open(path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(stub)

        self.save()
        return Revision(
            kind=kind, description=reason, version=self.version + 1, file=path
        )

    async def upgrade(self, connection: Connection) -> int:
        ordered = self.ordered_revisions
        successes = 0
        async with connection.transaction():
            for revision in ordered:
                if revision.version > self.version:
                    sql = revision.file.read_text("utf-8")
                    await connection.execute(sql)
                    successes += 1

        self.version += successes
        self.save()
        return successes

    def display(self) -> None:
        ordered = self.ordered_revisions
        for revision in ordered:
            if revision.version > self.version:
                print(1, revision)
                print(2, revision.file)
                sql = revision.file.read_text("utf-8")
                print(sql)


#
############
