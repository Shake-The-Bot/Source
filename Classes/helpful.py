from __future__ import annotations

from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from inspect import signature
from io import BytesIO
from json import dump, dumps, load, loads
from math import floor
from os import replace
from pathlib import Path
from random import choice, random, randrange
from re import Match, sub
from threading import Thread
from time import monotonic
from typing import *
from uuid import uuid4

import asyncpraw
from _collections_abc import dict_items, dict_values
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import Connection, InvalidCatalogNameError, Pool, connect, create_pool
from asyncpraw.models import Submission, Subreddit
from discord import *
from discord import Guild
from discord.ext.commands import *
from discord.player import AudioPlayer
from discord.ui import View
from PIL import Image, ImageDraw, ImageFont

from Classes.i18n import Locale, _, mo
from Classes.tomls import Config, Emojis, config, emojis
from Classes.types import Regex, TextFormat, TracebackType
from Classes.useful import MISSING, source_lines
from Extensions.Functions.Debug.error import error

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes import __version__

else:
    from discord.ext.commands import Bot as ShakeBot

    __version__ = MISSING

p = ThreadPoolExecutor(2)


__all__ = (
    "BotBase",
    "ShakeContext",
    "ShakeEmbed",
    "DatabaseProtocol",
    "Record",
    "Reddit",
    "ShakeCommand",
    "Category",
    "Migration",
)


############
#


""" A Class representing the custom Context (Inherits from discord.ext.commands.Context)
"""


class ShakeContext(Context):
    channel: VoiceChannel | TextChannel | Thread | DMChannel
    command: Command[Any, ..., Any]
    message: Message
    testing: bool
    bot: ShakeBot
    pool: DatabaseProtocol

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

    @utils.cached_property
    def replied_reference(self) -> Optional[MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, Message):
            return ref.resolved.to_reference()
        return None

    @utils.cached_property
    def replied_message(self) -> Optional[Message]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, Message):
            return ref.resolved
        return None

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
        stickers: Optional[Sequence[GuildSticker | StickerItem]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[str | int] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Message | MessageReference | PartialMessage] = MISSING,
        mention_author: Optional[bool] = False,
        view: Optional[View] = None,
        suppress_embeds: bool = False,
        ephemeral: bool = True,
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
                reference=self.replied_reference if reference is MISSING else reference,
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
        stickers: Optional[Sequence[GuildSticker | StickerItem]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[str | int] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = False,
        suppress_embeds: bool = False,
        view: Optional[View] = None,
        ephemeral: bool = True,
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

    async def chat(
        self,
        content: Optional[str] = None,
        tts: bool = False,
        embed: Optional[ShakeEmbed] = None,
        embeds: Optional[Sequence[ShakeEmbed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[GuildSticker | StickerItem]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[str | int] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = False,
        suppress_embeds: bool = False,
        view: Optional[View] = None,
        ephemeral: bool = True,
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
        if self.message.reference:
            if author := getattr(self.replied_message, "author", None):
                # author = ref.cached_message.author
                if not mention_author:
                    mention_author = (
                        author in self.message.mentions
                        and author.id not in self.message.raw_mentions
                    )
                    kwargs["mention_author"] = mention_author
            return await self.send(**kwargs)

        last_message = getattr(self.channel, "last_message", MISSING)
        if last_message not in [self.message, MISSING]:
            return await self.reply(**kwargs)
        else:
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

    """ Do I really need following things? """

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


""""""


class ShakeCommand:
    ctx: ShakeContext
    bot: ShakeBot

    def __init__(self, ctx: ShakeContext) -> None:
        self.ctx = ctx
        self.bot = ctx.bot


""" A Class representing the Base of the ShakeBot (Inherits from discord.ext.commands.AutoSharedBot)
yeah.. lazy rn"""


class BotBase(AutoShardedBot):
    user: ClientUser
    pool: Pool
    gpool: DatabaseProtocol
    boot: datetime
    gateway_handler: Any
    cache = dict()
    session: ClientSession
    ready_shards: Record
    bot_app_info: AppInfo

    def __init__(self, **options):
        owner_ids = options.pop("owner_ids")
        self.shake_id, *_ = owner_ids
        self.cache.setdefault("pages", dict())
        self.cache.setdefault("locales", dict())
        self.cache.setdefault("_data_batch", list())
        self.cache.setdefault(
            "testing", {1036952232719024129: None, 1103300342856286260: None}
        )
        self.cache.setdefault("context", deque(maxlen=100))
        self.cache.setdefault("tests", ExpiringCache(60 * 5))
        self.cache.setdefault("cached_posts", dict())
        self._session = None
        self._config = config
        self._emojis = emojis
        super().__init__(**options)
        self.ready_shards = Record(sequence=range(self.shard_count))

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
    ) -> ShakeContext | Context:
        context = await super().get_context(message, cls=cls)
        return context

    async def close(self):
        if hasattr(self, "scheduler"):
            if self.scheduler.running:
                self.scheduler.shutdown()

        if hasattr(self, "session"):
            if not self.session.closed:
                await self.session.close()

        if hasattr(self, "reddit"):
            if not self.reddit.client.requestor.loop.is_closed():
                await self.reddit.client.close()

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
        self.reddit: Reddit = Reddit()
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


""" Embed Helper
yeah.. lazy rn"""


class ShakeEmbed(Embed):
    """lazy"""

    def __init__(
        self,
        colour: Colour | int = MISSING,
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

    def advertise(self, bot: ShakeBot) -> ShakeEmbed:
        self.add_field(
            name="\u200b",
            value=TextFormat.blockquotes(bot.config.embed.footer),
            inline=False,
        )
        return self

    @classmethod
    def default(cls, ctx: ShakeContext | Interaction, **kwargs: Any) -> ShakeEmbed:
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
        ctx: ShakeContext | Interaction,
        colour: Optional[Colour | int] = None,
        **kwargs: Any,
    ) -> ShakeEmbed:
        bot: "ShakeBot" = (
            getattr(ctx, "bot", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "client", str(MISSING))
        )
        if description := kwargs.pop("description", None):
            kwargs["description"] = TextFormat.multiblockquotes(
                TextFormat.bold(f"{bot.emojis.hook} {bot.emojis.prefix} {description}")
            )
        instance = cls(colour=colour or 0x00CC88, **kwargs)
        instance.timestamp = None
        return instance

    @classmethod
    def to_error(
        cls,
        ctx: ShakeContext | Interaction,
        colour: Optional[Colour | int] = MISSING,
        **kwargs: Any,
    ) -> ShakeEmbed:
        colour = colour or 0xFF0000
        bot: "ShakeBot" = (
            getattr(ctx, "bot", str(MISSING))
            if isinstance(ctx, (ShakeContext, Context))
            else getattr(ctx, "client", str(MISSING))
        )
        if description := kwargs.pop("description", None):
            kwargs["description"] = TextFormat.multiblockquotes(
                TextFormat.bold(f"{bot.emojis.cross} {bot.emojis.prefix} {description}")
            )
        instance = cls(colour=colour, **kwargs)
        instance.timestamp = None
        return instance


""" Database Handler
yeah.. lazy rn"""


class Revisions(TypedDict):
    version: int
    base_url: str


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
        filename: str = "Schemas/revisions.json",
    ):
        self.filename: str = filename
        self.base_url = base_url
        self.type: Literal["guild", "bot"] = type
        self.root: Path = Path(filename).parent
        self.revisions: dict[int, Revision] = self.get_revisions(self.root)
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

    @staticmethod
    def get_revisions(root: Path) -> dict[int, Revision]:
        result: dict[int, Revision] = {}
        for file in root.glob("*.sql"):
            match = Regex.revision.value.match(file.name)
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

    @staticmethod
    async def ensure_uri_can_run(config, type: Literal["guild", "bot"]) -> bool:
        conn = connection = None
        conn: Connection = await connect(config.database.postgresql)
        try:
            connection: Connection = await connect(config.database.postgresql + type)
        except InvalidCatalogNameError:
            try:
                await conn.execute(
                    f'CREATE DATABASE "{type}" OWNER "{config.database.user}"'
                )
            except:
                raise
            finally:
                await conn.close()
        else:
            await conn.close()
            await connection.close()

        return True

    @staticmethod
    async def _create_pool(type: Literal["guild", "bot"] = "bot") -> Pool:
        def _encode_jsonb(value):
            return dumps(value)

        def _decode_jsonb(value):
            return loads(value)

        async def init(con):
            await con.set_type_codec(
                "jsonb",
                schema="pg_catalog",
                encoder=_encode_jsonb,
                decoder=_decode_jsonb,
                format="text",
            )

        await Migration.ensure_uri_can_run(config=config, type=type)
        return await create_pool(
            config.database.postgresql + type,
            init=init,
            command_timeout=60,
            max_size=20,
            min_size=20,
        )

    async def run(self, connection: Connection) -> int:
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


"""     Captcha Worker
yeah.. lazy rn"""


class Captcha:
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot
        self.colour = bot.config.embed.hex_color
        pass

    def proove(self, message: str) -> bool:
        if not message.lower() == self.password.lower():
            return False
        return True

    async def create(self):
        image = Image.new("RGBA", (325, 100), color=self.colour)  # (0, 0, 255))
        draw = ImageDraw.Draw(image)
        text = " ".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(5))
        W, H = (325, 100)
        w, h = draw.textsize(text, font=ImageFont.truetype(font="arial.ttf", size=60))
        draw.text(
            ((W - w) / 2, (H - h) / 2),
            text,
            font=ImageFont.truetype(font="arial.ttf", size=60),
            fill="#000000",
        )  # (90, 90, 90))
        filename = "captcha" + str(choice(range(10)))

        image = self.perform_operation(
            images=[image], grid_width=4, grid_height=4, magnitude=14
        )[0]

        draw = ImageDraw.Draw(image)
        for x, y in [
            ((0, randrange(20, 40)), (325, randrange(20, 40))),
            ((0, randrange(35, 55)), (325, randrange(35, 55))),
            ((0, randrange(60, 90)), (325, randrange(60, 90))),
        ]:
            draw.line([x, y], fill=(90, 90, 90, 90), width=randrange(3, 4))  #'#6176f5'

        noisePercentage = 0.60
        pixels = image.load()
        for i in range(image.size[0]):
            for j in range(image.size[1]):
                rdn = random()
                if rdn < noisePercentage:
                    pixels[i, j] = (60, 60, 60)

        image = image.resize((150, 50))
        self.password = "".join(text.split(" "))
        with BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            return File(fp=image_binary, filename=f"{filename}.png")

    def perform_operation(self, images, grid_width=4, grid_height=4, magnitude=14):
        """Something to make something between disortion and magic
        I don't really know but I needed to cut that part of code somewhere out"""
        w, h = images[0].size
        horizontal_tiles = grid_width
        vertical_tiles = grid_height
        width_of_square = int(floor(w / float(horizontal_tiles)))
        height_of_square = int(floor(h / float(vertical_tiles)))
        width_of_last_square = w - (width_of_square * (horizontal_tiles - 1))
        height_of_last_square = h - (height_of_square * (vertical_tiles - 1))
        dimensions = []

        for vertical_tile in range(vertical_tiles):
            for horizontal_tile in range(horizontal_tiles):
                if vertical_tile == (vertical_tiles - 1) and horizontal_tile == (
                    horizontal_tiles - 1
                ):
                    dimensions.append(
                        [
                            horizontal_tile * width_of_square,
                            vertical_tile * height_of_square,
                            width_of_last_square + (horizontal_tile * width_of_square),
                            height_of_last_square + (height_of_square * vertical_tile),
                        ]
                    )
                elif vertical_tile == (vertical_tiles - 1):
                    dimensions.append(
                        [
                            horizontal_tile * width_of_square,
                            vertical_tile * height_of_square,
                            width_of_square + (horizontal_tile * width_of_square),
                            height_of_last_square + (height_of_square * vertical_tile),
                        ]
                    )
                elif horizontal_tile == (horizontal_tiles - 1):
                    dimensions.append(
                        [
                            horizontal_tile * width_of_square,
                            vertical_tile * height_of_square,
                            width_of_last_square + (horizontal_tile * width_of_square),
                            height_of_square + (height_of_square * vertical_tile),
                        ]
                    )
                else:
                    dimensions.append(
                        [
                            horizontal_tile * width_of_square,
                            vertical_tile * height_of_square,
                            width_of_square + (horizontal_tile * width_of_square),
                            height_of_square + (height_of_square * vertical_tile),
                        ]
                    )

        last_column = []
        for i in range(vertical_tiles):
            last_column.append((horizontal_tiles - 1) + horizontal_tiles * i)

        last_row = range(
            (horizontal_tiles * vertical_tiles) - horizontal_tiles,
            horizontal_tiles * vertical_tiles,
        )

        polygons = []
        for x1, y1, x2, y2 in dimensions:
            polygons.append([x1, y1, x1, y2, x2, y2, x2, y1])

        polygon_indices = []
        for i in range((vertical_tiles * horizontal_tiles) - 1):
            if i not in last_row and i not in last_column:
                polygon_indices.append(
                    [i, i + 1, i + horizontal_tiles, i + 1 + horizontal_tiles]
                )

        for a, b, c, d in polygon_indices:
            dx = random.randint(-magnitude, magnitude)
            dy = random.randint(-magnitude, magnitude)
            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[a]
            polygons[a] = [x1, y1, x2, y2, x3 + dx, y3 + dy, x4, y4]
            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[b]
            polygons[b] = [x1, y1, x2 + dx, y2 + dy, x3, y3, x4, y4]
            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[c]
            polygons[c] = [x1, y1, x2, y2, x3, y3, x4 + dx, y4 + dy]
            x1, y1, x2, y2, x3, y3, x4, y4 = polygons[d]
            polygons[d] = [x1 + dx, y1 + dy, x2, y2, x3, y3, x4, y4]

        generated_mesh = []
        for i in range(len(dimensions)):
            generated_mesh.append([dimensions[i], polygons[i]])

        def do(image):
            return image.transform(
                image.size, Image.MESH, generated_mesh, resample=Image.BICUBIC
            )

        augmented_images = []

        for image in images:
            augmented_images.append(do(image))

        return augmented_images


"""     Pool Handler
yeah.. lazy rn"""


class ConnectionContextManager(Protocol):
    async def __aenter__(self) -> Connection:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        ...


class DatabaseProtocol(Protocol):
    async def execute(
        self, query: str, *args: Any, timeout: Optional[float] = None
    ) -> str:
        ...

    async def fetch(
        self, query: str, *args: Any, timeout: Optional[float] = None
    ) -> list[Any]:
        ...

    async def fetchrow(
        self, query: str, *args: Any, timeout: Optional[float] = None
    ) -> Optional[Any]:
        ...

    def acquire(self, *, timeout: Optional[float] = None) -> ConnectionContextManager:
        ...

    def release(self, connection: Connection) -> None:
        ...


"""A class representing functions with Voice
yeah.. lazy rn"""


class Voice:
    def __init__(self, ctx: ShakeContext, channel: VoiceChannel):
        self.ctx: ShakeContext = ctx
        self.bot: "ShakeBot" = ctx.bot
        self._channel: VoiceChannel = channel
        self._player: Optional[AudioPlayer] = None

    async def __await__(self, channel: Optional[VoiceChannel] = MISSING):
        try:
            channel = await VoiceChannelConverter().convert(
                self.ctx, channel or self._channel
            )
        except:
            raise
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

    async def connect(self, channel: Optional[VoiceChannel] = MISSING, **kwargs):
        try:
            voice = await (channel or self._channel).connect(
                reconnect=True, self_deaf=True, **kwargs
            )
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


""" Others  """


class Record:
    def __init__(self, sequence: Sequence) -> None:
        for extension in sequence:
            setattr(self, str(extension), False)

    def add(self, item) -> None:
        setattr(self, str(item), True)
        return

    def all(self) -> bool:
        return all([getattr(self, item, False) for item in self.__dict__.keys()])

    def added(self) -> dict:
        return {
            item: getattr(self, item, False)
            for item in self.__dict__.keys()
            if getattr(self, item, False)
        }


class ExpiringCache(dict):
    def __init__(self, seconds: float = 60 * 5):
        self.__ttl: float = seconds
        super().__init__()

    def __verify_cache_integrity(self):
        current_time = monotonic()
        to_remove = [
            k for (k, (v, t)) in super().items() if current_time > (t + self.__ttl)
        ]
        for k in to_remove:
            del self[k]

    def items(self) -> dict_items:
        self.__verify_cache_integrity()
        return [(k, v) for k, (v, t) in super().items()]

    def values(self) -> dict_values:
        self.__verify_cache_integrity()
        return [v for v, t in super().values()]

    def __contains__(self, key: str):
        self.__verify_cache_integrity()
        return super().__contains__(key)

    def __getitem__(self, key: str):
        self.__verify_cache_integrity()
        return super().__getitem__(key)[0]

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, (value, monotonic()))


class Category(Cog):
    bot: ShakeBot

    def __init__(self, bot: ShakeBot, cog: Optional[Cog] = None) -> None:
        self.bot = bot

    @property
    def description(self) -> str:
        raise NotImplemented

    @property
    def emoji(self) -> PartialEmoji:
        raise NotImplemented

    @property
    def label(self) -> str:
        raise NotImplemented

    @property
    def title(self) -> str:
        raise NotImplemented

    @property
    def describe(self) -> bool:
        raise NotImplemented


class Reddit:
    def __init__(self):
        self.posts = set()
        self.client = asyncpraw.Reddit(
            client_id=config.reddit.client_id,
            client_secret=config.reddit.client_secret,
            username=config.reddit.username,
            password=config.reddit.password,
            user_agent="Shake/{}".format(__version__),
        )

    async def __await__(self, ctx: ShakeContext):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.guild: Guild = ctx.guild
        self.guild_posts = ctx.bot.cache["cached_posts"].setdefault(
            ctx.guild.id, deque(maxlen=1000)
        )
        await self.prepare()

    async def prepare(self):
        if not bool(len(self.posts)):
            pass
            return

        for post in self.posts:
            pass

    async def create(self, ctx, subreddits):
        subs: Subreddit = await self.client.subreddit("+".join(subreddits), fetch=False)
        posts = [
            post
            async for post in subs.new(limit=25)
            if not post.over_18 and not post in self.guild_posts
        ]
        for post in posts:
            self.posts.add(post)
        return posts

    @classmethod
    def expire(self, post: Submission):
        self.guild_posts.add(post)

    async def get_post(self, ctx: ShakeContext, subreddit):
        if not bool(len(self.posts)):
            await self.create(ctx, subreddit)

        for post in self.posts:
            if post in self.guild_posts:
                continue
            self.expire(ctx, post)
            return post

        post = choice(list(await self.create(ctx, subreddit)))
        self.expire(ctx, post)
        return post


#
############
