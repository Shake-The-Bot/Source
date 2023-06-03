from enum import Enum
from functools import partial
from io import BytesIO
from math import floor
from os import getcwd, listdir
from os.path import isdir, isfile
from random import choice as rchoice
from random import random, randrange
from sys import exc_info
from time import monotonic
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
    _SpecialForm,
    _type_check,
)
from urllib.parse import quote

from _collections_abc import dict_items
from aiohttp import ClientSession
from asyncpg import Connection, InvalidCatalogNameError, connect
from dateutil.relativedelta import relativedelta
from discord import (
    ClientException,
    FFmpegPCMAudio,
    File,
    Guild,
    Interaction,
    Member,
    PartialEmoji,
    TextChannel,
    VoiceChannel,
)
from discord.abc import T
from discord.ext.commands import ChannelNotFound as _ChannelNotFound
from discord.ext.commands import Context, VoiceChannelConverter
from discord.ext.commands.errors import ExtensionAlreadyLoaded, ExtensionNotLoaded
from discord.player import AudioPlayer
from PIL import Image, ImageDraw, ImageFont

from Classes.converter import ValidCog
from Classes.exceptions import ChannelNotFound, NoDumpingSpots, NotVoted
from Classes.i18n import _, current
from Classes.tomls import config

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import ShakeContext, ShakeEmbed

else:
    from discord import Embed as ShakeEmbed
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext

__all__ = (
    "ensure_uri_can_run",
    "captcha",
    "perform_operation",
    "human_join",
    "source_lines",
    "high_level_function",
    "calc",
    "aboveme",
    "counting",
    "votecheck",
    "Ready",
    "dump",
    "DatabaseProtocol",
    "FormatTypes",
    "cogshandler",
    "MISSING",
    "RTFM_PAGE_TYPES",
    "choice",
    "ExpiringCache",
    "TextFormat",
    "TracebackType",
)


b = lambda t: TextFormat.format(t, type=FormatTypes.bold)

try:
    raise TypeError
except TypeError:
    tb = exc_info()[2]
    TracebackType = type(tb)
    FrameType = type(tb.tb_frame)
    tb = None
    del tb


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return "..."


MISSING: Any = _MissingSentinel()


@_SpecialForm
def Missing(self, parameters):
    """Missing type.

    Missing[X] is equivalent to Union[X, MISSING].
    """
    arg = _type_check(parameters, f"{self} requires a single type.")
    return Union[arg, type(MISSING)]


RTFM_PAGE_TYPES = {
    "stable": "https://discordpy.readthedocs.io/en/stable",
    "latest": "https://discordpy.readthedocs.io/en/latest",
    "python": "https://docs.python.org/3",
}

""""    Image    """


async def captcha(bot):
    # creation & text
    image = Image.new(
        "RGBA", (325, 100), color=bot.config.embed.hex_colour
    )  # (0, 0, 255))
    draw = ImageDraw.Draw(image)
    text = " ".join(rchoice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(5))
    W, H = (325, 100)
    w, h = draw.textsize(text, font=ImageFont.truetype(font="arial.ttf", size=60))
    draw.text(
        ((W - w) / 2, (H - h) / 2),
        text,
        font=ImageFont.truetype(font="arial.ttf", size=60),
        fill="#000000",
    )  # (90, 90, 90))
    filename = "captcha" + str(rchoice(range(10)))

    image = perform_operation(
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
    with BytesIO() as image_binary:
        image.save(image_binary, "PNG")
        image_binary.seek(0)
        return File(fp=image_binary, filename=f"{filename}.png"), "".join(
            text.split(" ")
        )


def perform_operation(images, grid_width=4, grid_height=4, magnitude=14):
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


USER = r"<@!?(\d+)>"
ROLE = r"<@&(\d+)>"
CHANNEL = r"<#(\d+)>"
COMMAND = r"<\/([-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32})/:(\d+)>"

"""     Sequence    """


class Ready(object):
    def __init__(self, sequence: Sequence) -> None:
        for extension in sequence:
            setattr(self, str(extension), False)

    def ready(self, item) -> None:
        setattr(self, str(item), True)
        return

    def all_ready(self) -> bool:
        return all([getattr(self, item, False) for item in self.__dict__.keys()])

    def readies(self) -> dict:
        return {
            item: getattr(self, item, False)
            for item in self.__dict__.keys()
            if getattr(self, item, False)
        }


def choice(seq):
    """Choose a random element from a non-empty sequence.
    if an empty sequence is given, None is returned"""
    # raises IndexError if seq is empty
    if len(seq) == 0:
        return None
    else:
        return rchoice(seq)


"""     Text     """


def string(
    text: str,
    *format: str,
    front: Optional[Union[str, bool]] = None,
    end: Optional[Union[str, bool]] = None,
    iterate: bool = True,
):
    front = (
        ""
        if front is False
        else "".join(front)
        if not iterate and front
        else "".join(format)
    )
    end = (
        ""
        if end is False
        else "".join(end)
        if not iterate and end
        else "".join(reversed(format))
    )
    return f"{front}{str(text)}{end}"


class FormatTypes(Enum):
    italics: Callable[[str], str] = lambda t: string(t, "_")
    bold: Callable[[str], str] = lambda t: string(t, "**")
    bolditalics: Callable[[str], str] = lambda t: string(t, "***")
    underline: Callable[[str], str] = lambda t: string(t, "__")
    underlinebold: Callable[[str], str] = lambda t: string(t, "__", "**")
    underlinebolditalics: Callable[[str], str] = lambda t: string(t, "__", "***")
    strikethrough: Callable[[str], str] = lambda t: string(t, "~~")
    codeblock: Callable[[str], str] = lambda t: string(t, "`")
    multicodeblock: Callable[[str], str] = lambda t, f=None: string(
        t, front="```" + (f if f else ""), end="```", iterate=False
    )
    blockquotes: Callable[[str], str] = lambda t: string(t, "> ", end=False)
    hyperlink: Callable[[str, str], str] = (
        lambda t, l: "[" + str(t) + "]" + "(" + str(l) + ")"
    )
    multiblockquotes: Callable[[str], str] = lambda t: string(t, ">>> ", end=False)
    big: Callable[[str], str] = lambda t: string(t, "# ", end=False)
    small: Callable[[str], str] = lambda t: string(t, "## ", end=False)
    tiny: Callable[[str], str] = lambda t: string(t, "### ", end=False)
    spoiler: Callable[[str], str] = lambda t: string(t, "||")
    list: Callable[[str, int], str] = lambda t, indent=1: string(
        t, (" " * indent * 2) + "-", end=False
    )


class TextFormat:
    @staticmethod
    def format(text: str, type: FormatTypes, *args, **kwargs):
        return type(t=text, *args, **kwargs)


def human_join(
    seq: Sequence[str],
    delimiter: str = ", ",
    final: Literal["or", "and"] = "and",
    joke: bool = False,
) -> str:
    if joke:
        return ""
    _("or")
    _("and")  # „Just in case gettext gets this“
    size = len(seq)
    if size == 0:
        return ""
    if size == 1:
        return seq[0]
    if size == 2:
        return f"{seq[0]} {final} {seq[1]}"
    return delimiter.join(seq[:-1]) + f" {final} {seq[-1]}"


def source_lines(path: Optional[str] = None) -> int:
    path = path or getcwd()

    def _iterate_source_line_counts(_path: str) -> Iterator[int]:
        for file in listdir(_path):
            __path: str = f"{_path}/{file}"

            if isdir(__path):
                yield from _iterate_source_line_counts(__path)

            if not isfile(__path):
                continue

            if file.endswith((".py")) and not file.startswith("."):
                with open(__path, encoding="utf8") as f:
                    yield len(
                        [
                            line
                            for line in f.readlines()
                            if not line.strip().startswith("#") and not "import" in line
                        ]
                    )

    return sum(_iterate_source_line_counts(path))


def Duration(duration: str) -> Optional[relativedelta]:
    """
    Convert a `duration` string to a relativedelta object.
    The following symbols are supported for each unit of time:

    - years: `Y`, `y`, `year`, `years`
    - months: `m`, `month`, `months`
    - weeks: `w`, `W`, `week`, `weeks`
    - days: `d`, `D`, `day`, `days`
    - hours: `H`, `h`, `hour`, `hours`
    - minutes: `M`, `minute`, `minutes`
    - seconds: `S`, `s`, `second`, `seconds`

    The units need to be provided in descending order of magnitude.
    Return None if the `duration` string cannot be parsed according to the symbols above.
    """
    regex = compile(
        r"((?P<years>\d+?) ?(years|year|Y|y) ?)?"
        r"((?P<months>\d+?) ?(months|month|m) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|W|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|M) ?)?"
        r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
    )
    match = regex.fullmatch(duration)
    if not match:
        return None

    duration_dict = {
        unit: int(amount) for unit, amount in match.groupdict(default=0).items()
    }
    delta = relativedelta(**duration_dict)

    return delta


# outdated
def high_level_function():
    with open("POTFILES.in") as mfile:
        paths = mfile.read().splitlines()
        for path in paths:
            with open(f"{path}", "r+") as file:
                lines = file.read().splitlines()
                newlines = lines.copy()
                done = 0
                for idx, line in enumerate(lines):
                    if "@" in line and (".group" in line or ".command" in line):
                        newlines.insert(idx + 1, "    @locale_doc")
                        done += 1
                file.seek(0)
                file.write("\n".join(newlines))
                file.truncate()


"""     Numbers     """


def calc(expression):
    try:
        result = eval(expression)
    # division by zero
    except ZeroDivisionError:
        result = "Undefined (division by zero)"
    # invalid expressions
    except:
        result = "Invalid expression"
    return result


"""     Timing      """


class ExpiringCache(dict):
    def __init__(self, seconds: float):
        self.__ttl: float = seconds
        super().__init__()

    def __verify_cache_integrity(self):
        # Have to do this in two steps...
        current_time = monotonic()
        to_remove = [
            k for (k, (v, t)) in self.items() if current_time > (t + self.__ttl)
        ]
        for k in to_remove:
            del self[k]

    def items(self) -> dict_items:
        return [(k, v) for k, (v, t) in super().items()]

    def __contains__(self, key: str):
        self.__verify_cache_integrity()
        return super().__contains__(key)

    def __getitem__(self, key: str):
        self.__verify_cache_integrity()
        return super().__getitem__(key)[0]

    def __setitem__(self, key: str, value: Any):
        super().__setitem__(key, (value, monotonic()))


"""     Others      """


async def votecheck(ctx: Optional[Union[ShakeContext, Context, Interaction]] = MISSING):
    user = (
        getattr(ctx, "author", str(MISSING))
        if isinstance(ctx, (ShakeContext, Context))
        else getattr(ctx, "user", str(MISSING))
    )
    bot: ShakeBot = (
        getattr(ctx, "bot", str(MISSING))
        if isinstance(ctx, (ShakeContext, Context))
        else getattr(ctx, "client", str(MISSING))
    )
    header = {"Authorization": str(config.other.topgg.token)}
    params = {"userId": user.id}

    async with bot.session as session:
        try:
            response = await session.get(
                f"https://top.gg/api/bots/{bot.id}/check", headers=header, params=params
            )
            data = await response.json(content_type=None)

            if data["voted"] == 1:
                return True
            NotVoted()
        except:
            raise


class Categorys(Enum):
    Functions = "functions"
    Gimmicks = "gimmicks"
    Information = "information"
    # load = 'inviting'
    # load = 'leveling'
    Moderation = "moderation"
    # load = 'notsafeforwork'
    Other = "other"


class Methods(Enum):
    load = partial(ShakeBot.load_extension)
    unload = partial(ShakeBot.unload_extension)
    reload = partial(ShakeBot.reload_extension)


async def cogshandler(
    ctx: ShakeContext, extensions: list[ValidCog], method: Methods
) -> None:
    async def handle(method: Methods, extension: ValidCog) -> str:
        function = method.value
        error = None

        try:
            await function(ctx.bot, extension)

        except ExtensionNotLoaded as error:
            if method is method.reload:
                func = await handle(method.load, extension)
                return func
            if method is method.unload:
                return None
            return error

        except (ExtensionAlreadyLoaded,) as error:
            if method is method.load:
                return None
            return error

        except Exception as err:
            return err

        return None

    embed = ShakeEmbed()

    failures: int = 0
    for i, extension in enumerate(extensions, 1):
        handling = await handle(method, extension)
        error = getattr(handling, "original", handling) if handling else MISSING

        ext = f"`{extension}`"
        name = f"` {i}. ` {ext}"
        if error:
            failures += 1
            value = "> ❌ {}".format(error.replace(extension, ext))
        else:
            value = f"> ☑️ {method.name.lower().capitalize()}ed"
        embed.add_field(name=name, value=value)

    embed.description = f"**{len(extensions) - failures} / {len(extensions)} extensions successfully {method.name.lower()}ed.**"
    return embed


async def dump(
    content: str, session: ClientSession, lang: Optional[str] = "txt"
) -> Optional[str]:
    async with session.post(
        "https://hastebin.com/documents",
        data=content,
        headers={
            "Authorization": "Bearer 27e4168ab6efb5fc22135cdea73f9f04b6581de99785b84daf1c2c3803e61e28c0f4881710e29cc0e9706b35a11cff8e46ef2b00999db3010ee1dc818f9be255"
        },
    ) as post:
        if 200 <= post.status < 400:
            text = await post.text()
            return f"https://hastebin.com/share/{text[8:-2]}"

    async with session.post(
        "https://hastepaste.com/api/create",
        data=f"raw=false&text={quote(content)}",
        headers={
            "User-Agent": "Shake",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    ) as post:
        if 200 <= post.status < 400:
            text = await post.text()
            return text

    async with session.post("https://api.mystb.in/paste", data=content) as post:
        if 200 <= post.status < 400:
            return "https://mystb.in/" + (await post.json())["pastes"][0]["id"]

    async with session.post(
        "https://bin.readthedocs.fr/new", data={"code": content, "lang": lang}
    ) as post:
        if 200 <= post.status < 400:
            text = post.url
            return text

    raise NoDumpingSpots("All tried hosts did not work")


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


class Voice:
    """
    A class representing functions with Voice
    """

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
        except _ChannelNotFound:
            raise ChannelNotFound("I could not find the given VoiceChannel")
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


class aboveme:
    def __init__(
        self,
        bot: ShakeBot,
        member: Member,
        channel: TextChannel,
        guild: Guild,
        content: str,
    ):
        self.bot: ShakeBot = bot
        self.pool: DatabaseProtocol = bot.gpool
        self.member: Member = member
        self.content: str = content
        self.channel: TextChannel = channel
        self.guild: Guild = guild
        self.testing = any(
            x.id in set(self.bot.testing.keys()) for x in [channel, guild, member]
        )

    async def phrase_check(self, content: str, phrases: List[str]):
        if content.strip() in phrases:
            return False
        return True

    async def syntax_check(self, content: str):
        if not content.lower().startswith(self.trigger.lower()):
            return False

        if not content.lower().removeprefix(self.trigger.lower()).strip():
            return False
        return True

    async def member_check(self, user_id: int):
        if self.testing and await self.bot.is_owner(self.member):
            return True
        elif user_id == self.member.id:
            return False
        return True

    async def __await__(self) -> Tuple[Optional[ShakeEmbed], bool, bool]:
        async with self.pool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT * FROM aboveme WHERE channel_id = $1",
                self.channel.id,
            )

        user_id: int = record["user_id"]
        count: int = record["count"] or 0
        phrases: List[str] = record["phrases"] or []
        hardcore: bool = record["hardcore"]

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        self.trigger: str = _("the one above me")

        embed = ShakeEmbed(timestamp=None)

        delete = bad_reaction = xyz = False

        if not await self.member_check(user_id):
            embed.description = _(
                """{user} ruined it {facepalm} **You can't show off several times in a row**.
                Someone should still go on."""
            ).format(
                user=self.member.mention,
                facepalm=str(PartialEmoji(name="facepalm", id=1038177759983304784)),
            )

            if hardcore:
                embed.description = _(
                    """{user} you are not allowed show off multiple numbers in a row."""
                ).format(user=self.member.mention)
                delete = bad_reaction = True

        elif not await self.syntax_check(self.content):
            embed.description = _(
                "{emoji} Your message should start with „{trigger}“ and should make sense."
            ).format(
                emoji="<a:nananaa:1038185829631266981>",
                trigger=b(self.trigger.capitalize()),
            )
            delete = bad_reaction = True

        elif not await self.phrase_check(self.content, phrases):
            embed.description = _(
                "{emoji} Your message should be something new"
            ).format(
                emoji="<a:nananaa:1038185829631266981>",
            )
            delete = bad_reaction = True

        else:
            xyz = True
            embed = None

        async with self.pool.acquire() as connection:
            p = phrases.copy()
            if len(p) >= 10:
                for i in range(len(p[10:-1])):
                    p.pop(i)
            p.insert(0, self.content)

            await connection.execute(
                "UPDATE aboveme SET user_id = $2, phrases = $3, count = $4 WHERE channel_id = $1;",
                self.channel.id,
                self.member.id,
                phrases,
                count + 1 if xyz else count,
            )
        return embed, delete, bad_reaction


class counting:
    def __init__(
        self,
        bot: ShakeBot,
        member: Member,
        channel: TextChannel,
        guild: Guild,
        content: str,
    ):
        self.bot: ShakeBot = bot
        self.pool: DatabaseProtocol = bot.gpool
        self.member: Member = member
        self.content: str = content
        self.channel: TextChannel = channel
        self.guild: Guild = guild
        self.testing = any(
            x.id in set(self.bot.testing.keys()) for x in [channel, guild, member]
        )

    def tens(self, count: int, last: int = 1):
        if 0 <= count <= 10:
            return 1
        if len(str(count)) <= last:
            last = len(str(count)) - 1
        digits = [int(_) for _ in str(count)]
        for zahl in range(last):
            zahl = zahl + 1
            digits[-zahl] = 0
        return int("".join(str(x) for x in digits))

    async def syntax_check(self, content: str):
        if not content.isdigit():
            return False
        return True

    async def check_number(self, content: str, count: int):
        if not int(content) == count + 1:
            return False
        return True

    async def member_check(self, user_id: int):
        if self.testing and await self.bot.is_owner(self.member):
            return True
        elif user_id == self.member.id:
            return False
        return True

    async def __await__(self):
        async with self.pool.acquire() as connection:
            record = await connection.fetchrow(
                "SELECT * FROM counting WHERE channel_id = $1",
                self.channel.id,
            )

        streak: int = record["streak"] or 0
        best: int = record["best"] or 0
        user_id: int = record["user_id"]
        hardcore: bool = record["hardcore"]
        goal: int = record["goal"]
        count: int = record["count"] or 0
        numbers: bool = record["numbers"]

        backup: int = self.tens(count)
        reached: bool = False

        current.set(
            await self.bot.locale.get_guild_locale(self.guild.id, default="en-US")
        )

        embed = ShakeEmbed(timestamp=None)
        delete = xyz = False
        bad_reaction = 0

        if not await self.syntax_check(self.content):
            if numbers:
                embed.description = _(
                    "{emoji} You're not allowed to use anything except numbers here"
                ).format(emoji="<a:nananaa:1038185829631266981>")
                delete = True
                bad_reaction = 1
            else:
                return None, None, None

        elif not await self.member_check(user_id):
            embed.description = _(
                "{user} you are not allowed to count multiple numbers in a row."
            ).format(user=self.member.mention)

            delete = True
            if hardcore:
                pass
                # embed.description = _(
                #     """{user} ruined it at **{count}** {facepalm} **You can't count multiple numbers in a row**. The __next__ number {verb} ` {last} `. {streak}""").format(
                #             user=self.member.mention, count=record['count'], facepalm='<:facepalm:1038177759983304784>',
                #             streak=_("**You've topped your best streak with {} 🔥**".format(self.streak)) if self.streak > self.best_streak else '',
                #             verb=(_("is") if not last_ten == record['count'] else _("remains")), last=last_ten)
                # async with db.acquire():
                #     await db.execute(
                #         'UPDATE counting SET user_id = $2, count = $3, streak = 0, best_streak = $4 WHERE channel_id = $1;',
                #         record['channel_id'], self.member.id, last_ten, self.streak if self.streak>self.best_streak else self.best_streak
                #     )
                # delete = bad_reaction = True

        elif not await self.check_number(self.content, count):
            if int(count) in [0, 1]:
                embed.description = _(
                    (
                        "Incorrect number! The __next__ number is ` {last} `. "
                        "**No stats have been changed since the current number was {count}.**"
                        ""
                    )
                ).format(last=backup, count=int(record["count"]) - 1)
                bad_reaction = 2
            else:
                s = ""
                if streak > best:
                    s = b(
                        _("You've topped your best streak with {} numbers 🔥").format(
                            self.streak
                        )
                    )

                embed.description = _(
                    (
                        "{user} ruined it at **{count}** {facepalm}. "
                        "**You apparently can't count properly**. "
                        "The __next__ number is ` {last} `. {streak}"
                    )
                ).format(
                    user=self.member.mention,
                    count=record["count"],
                    facepalm="<:facepalm:1038177759983304784>",
                    streak=s,
                    last=backup,
                )
                bad_reaction = 1

        else:
            xyz = True

            if goal and count + 1 >= config["goal"]:
                reached = True
                embed.description = b(
                    _(
                        "You've reached your goal of {goal} {emoji} Congratulations!"
                    ).format(goal=config["goal"], emoji="<a:tadaa:1038228851173625876>")
                )
            else:
                embed = None

        async with self.pool.acquire() as connection:
            s = streak + 1 if xyz else streak
            await connection.execute(
                "UPDATE counting SET user_id = $2, count = $3, streak = $4, best = $5, goal = $6 WHERE channel_id = $1;",
                self.channel.id,
                self.member.id,
                count + 1 if xyz else count,
                s,
                s if s > best else best,
                None if reached else goal,
            )
        return embed, delete, bad_reaction


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
