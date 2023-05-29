from enum import Enum
from functools import partial
from io import BytesIO
from math import floor
from os import getcwd, listdir, path
from random import choice as rchoice
from random import random, randrange
from threading import Timer
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterator,
    Literal,
    Optional,
    Sequence,
    Union,
    _SpecialForm,
    _type_check,
)

from dateutil.relativedelta import relativedelta
from discord import File, Interaction
from discord.ext.commands import Context
from discord.ext.commands.errors import (
    ExtensionAlreadyLoaded,
    ExtensionNotFound,
    ExtensionNotLoaded,
    NoEntryPointError,
)
from numpy import zeros
from PIL import Image, ImageDraw, ImageFont

from Classes.converter import ValidCog
from Classes.exceptions import NotVoted
from Classes.i18n import _
from Classes.tomls import Config
from Exts.extensions import extensions

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import ShakeContext, ShakeEmbed

else:
    from discord import Embed as ShakeEmbed
    from discord.ext.commands import Bot as ShakeBot
    from discord.ext.commands import Context as ShakeContext

__all__ = (
    'captcha', 'perform_operation', 'human_join', 'source_lines', 
    'levenshtein', 'high_level_function', 'calc', 'votecheck', 'Ready',
    'cogshandler', 'MISSING', 'RTFM_PAGE_TYPES', 'choice', 'TimedDict'
)

config = Config('config.toml')
    

class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'

MISSING: Any = _MissingSentinel()

@_SpecialForm
def Missing(self, parameters):
    """Missing type.

    Missing[X] is equivalent to Union[X, MISSING].
    """
    arg = _type_check(parameters, f"{self} requires a single type.")
    return Union[arg, type(MISSING)]


RTFM_PAGE_TYPES = {
    'stable': 'https://discordpy.readthedocs.io/en/stable',
    'latest': 'https://discordpy.readthedocs.io/en/latest',
    'python': 'https://docs.python.org/3',
}

""""    Image    """

async def captcha(bot):
    # creation & text
    image = Image.new("RGBA", (325, 100), color=bot.config.embed.hex_colour)#(0, 0, 255))
    draw = ImageDraw.Draw(image)
    text = ' '.join(rchoice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(5))
    W, H = (325, 100)
    w, h = draw.textsize(text, font=ImageFont.truetype(font="arial.ttf", size=60))
    draw.text(((W - w) / 2, (H - h) / 2), text, font=ImageFont.truetype(font="arial.ttf", size=60), fill='#000000')#(90, 90, 90))    
    filename = 'captcha'+str(rchoice(range(10)))

    image = perform_operation(images=[image], grid_width=4, grid_height=4, magnitude=14)[0]

    draw = ImageDraw.Draw(image)
    for x, y in [((0, randrange(20, 40)), (325, randrange(20, 40))), ((0, randrange(35, 55)), (325, randrange(35, 55))), ((0, randrange(60, 90)), (325, randrange(60, 90)))]:
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
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return File(fp=image_binary, filename=f'{filename}.png'), "".join(text.split(" "))

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
            if vertical_tile == (vertical_tiles - 1) and horizontal_tile == (horizontal_tiles - 1):
                dimensions.append([
                    horizontal_tile * width_of_square, vertical_tile * height_of_square,
                    width_of_last_square + (horizontal_tile * width_of_square), height_of_last_square + (height_of_square * vertical_tile)
                ])
            elif vertical_tile == (vertical_tiles - 1):
                dimensions.append([
                    horizontal_tile * width_of_square, vertical_tile * height_of_square,
                    width_of_square + (horizontal_tile * width_of_square), height_of_last_square + (height_of_square * vertical_tile)
                ])
            elif horizontal_tile == (horizontal_tiles - 1):
                dimensions.append([
                    horizontal_tile * width_of_square, vertical_tile * height_of_square,
                    width_of_last_square + (horizontal_tile * width_of_square), height_of_square + (height_of_square * vertical_tile)
                ])
            else:
                dimensions.append([
                    horizontal_tile * width_of_square, vertical_tile * height_of_square,
                    width_of_square + (horizontal_tile * width_of_square), height_of_square + (height_of_square * vertical_tile)
                ])

    last_column = []
    for i in range(vertical_tiles):
        last_column.append((horizontal_tiles-1)+horizontal_tiles*i)

    last_row = range((horizontal_tiles * vertical_tiles) - horizontal_tiles, horizontal_tiles * vertical_tiles)

    polygons = []
    for x1, y1, x2, y2 in dimensions:
        polygons.append([x1, y1, x1, y2, x2, y2, x2, y1])

    polygon_indices = []
    for i in range((vertical_tiles * horizontal_tiles) - 1):
        if i not in last_row and i not in last_column:
            polygon_indices.append([i, i + 1, i + horizontal_tiles, i + 1 + horizontal_tiles])

    for a, b, c, d in polygon_indices:
        dx = random.randint(-magnitude, magnitude)
        dy = random.randint(-magnitude, magnitude)
        x1, y1, x2, y2, x3, y3, x4, y4 = polygons[a]
        polygons[a] = [x1, y1, x2, y2, x3 + dx, y3 + dy, x4, y4]
        x1, y1, x2, y2, x3, y3, x4, y4 = polygons[b]
        polygons[b] = [x1, y1, x2 + dx, y2 + dy, x3, y3, x4, y4]
        x1, y1, x2, y2, x3, y3, x4, y4 = polygons[c]
        polygons[c] = [x1, y1,x2, y2, x3, y3, x4 + dx, y4 + dy]
        x1, y1, x2, y2, x3, y3, x4, y4 = polygons[d]
        polygons[d] = [x1 + dx, y1 + dy, x2, y2, x3, y3, x4, y4]

    generated_mesh = []
    for i in range(len(dimensions)):
        generated_mesh.append([dimensions[i], polygons[i]])

    def do(image):
        return image.transform(image.size, Image.MESH, generated_mesh, resample=Image.BICUBIC)

    augmented_images = []

    for image in images:
        augmented_images.append(do(image))

    return augmented_images

USER = r'<@!?(\d+)>'
ROLE = r'<@&(\d+)>'
CHANNEL = r'<#(\d+)>'
COMMAND = r'<\/([-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32})/:(\d+)>'

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
                for item in self.__dict__.keys() if getattr(self, item, False)
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
def string(text: str, *format: str, front: Optional[Union[str, bool]] = None, end: Optional[Union[str, bool]] = None, iterate: bool = True):
    front = '' if front is False else ''.join(front) if not iterate and front else ''.join(format)
    end = '' if end is False else ''.join(end) if not iterate and end else ''.join(reversed(format))
    return f"{front}{str(text)}{end}"

class FormatTypes(Enum):
    italics: Callable[[str], str] = lambda t: string(t, '_')
    bold: Callable[[str], str] = lambda t: string(t, '**') 
    bolditalics: Callable[[str], str] = lambda t: string(t, '***')
    underline: Callable[[str], str] = lambda t: string(t, '__')
    underlinebold: Callable[[str], str] = lambda t: string(t, '__', '**')
    underlinebolditalics: Callable[[str], str] = lambda t: string(t, '__', '***')
    strikethrough: Callable[[str], str] = lambda t: string(t, '~~')
    codeblock: Callable[[str], str] = lambda t: string(t, '`')
    multicodeblock: Callable[[str], str] = lambda t, f=None: string(t, front='```'+f if f else '', end='````', iterate=False)
    blockquotes: Callable[[str], str] = lambda t: string(t, '> ', end=False)
    hyperlink: Callable[[str, str], str] = lambda t, l: '['+str(t)+']' + '('+str(l)+')'
    multiblockquotes: Callable[[str], str] = lambda t: string(t, '>>> ', end=False)
    big: Callable[[str], str] = lambda t: string(t, '# ', end=False)
    small: Callable[[str], str] = lambda t: string(t, '## ', end=False)
    tiny: Callable[[str], str] = lambda t: string(t, '### ', end=False)
    spoiler: Callable[[str], str] = lambda t: string(t, '||')
    list: Callable[[str, int], str] = lambda t, indent=1: string(t, (' '*indent*2)+'-', end=False)  

class TextFormat:
    @staticmethod
    def format(text: str, type: FormatTypes, *args, **kwargs):
        return type(t=text, *args, **kwargs)

def human_join(seq: Sequence[str], delimiter: str = ', ', final: Literal['or', 'and'] = 'and', joke: bool = False) -> str:
    if joke:
        return ''
    _('or'); _('and') # „Just in case gettext gets this“
    size = len(seq)
    if size == 0:
        return ''
    if size == 1:
        return seq[0]
    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'
    return delimiter.join(seq[:-1]) + f' {final} {seq[-1]}'


def source_lines(root: Optional[str] = None) -> int:
    root = root or getcwd()
    def _iterate_source_line_counts(root: str) -> Iterator[int]:
        for child in listdir(root):
            _path = f"{root}/{child}"
            if path.isdir(_path):
                yield from _iterate_source_line_counts(_path)
            if (child.startswith(".") or child.endswith('.toml') or child in ['LICENSE', 'README.md']): 
                continue
            else:
                if _path.endswith((".py")):
                    with open(_path, encoding="utf8") as f:
                        yield len(f.readlines())
    return sum(_iterate_source_line_counts(root))


def levenshtein(one: str, two: str, ratio_calc: Optional[bool] = False):
    rows, columns = (len(one) + 1, len(two) + 1)
    distance = zeros((rows, columns), dtype = int)
    
    for i in range(1, rows):
        for k in range(1, columns):
            distance[i][0], distance[0][k] = (i, k)
             
    for column in range(1, columns):
        for row in range(1, rows):
            if one[row - 1] == two[column - 1]:
                cost = 0
            else:
                if ratio_calc: 
                    cost = 2
                else: 
                    cost = 1
            distance[row][column] = min(distance[row-1][column] + 1, distance[row][column-1] + 1, distance[row-1][column-1] + cost)

    if ratio_calc: 
        return ((len(one)+len(two)) - distance[row][column]) / (len(one)+len(two))
    else: 
        return distance[row][column]

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

    duration_dict = {unit: int(amount) for unit, amount in match.groupdict(default=0).items()}
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

class TimedDict(dict):
    def __init__(self, limit: int):
        self.__timers = dict()
        self.limit = limit
        super().__init__()
    
    def __setitem__(self, __key: Any, __value: Any) -> None:
        if __key in self:
            timer: Timer = self.__timers.get(__key, None)
            if timer is not None:
                timer.cancel()
                del self.__timers[__key]
        self._timer(__key)
        return super().__setitem__(__key, __value)

    def __delitem__(self, __key: Any) -> None:
        timer: Timer = self.__timers.get(__key, None)
        if timer is not None:
            timer.cancel()
            del self.__timers[__key]
        return super().__delitem__(__key)

    def _expired(self, __key: Any):
        if __key in self:
            self.__delitem__(__key)

    def _timer(self, __key: Any):
        timer = Timer(self.limit, self._expired, args=[__key])
        timer.daemon = True
        timer.start()
        self.__timers[__key] = timer


"""     Others      """

async def votecheck(ctx: Optional[Union[ShakeContext, Context, Interaction]] = MISSING):
    user = getattr(ctx, 'author', str(MISSING)) if isinstance(ctx, (ShakeContext, Context)) else getattr(ctx, 'user', str(MISSING))
    bot: ShakeBot = getattr(ctx, 'bot', str(MISSING)) if isinstance(ctx, (ShakeContext, Context)) else getattr(ctx, 'client', str(MISSING))
    header = {"Authorization": str(config.other.topgg.token)}
    params = {"userId": user.id}

    async with bot.session as session:
        try:
            response = await session.get(f"https://top.gg/api/bots/{bot.id}/check", headers=header, params=params)
            data = await response.json(content_type=None)

            if data['voted'] == 1:
                return True
            NotVoted()
        except:
            raise

class Categorys(Enum):
    Functions = 'functions'
    Gimmicks = 'gimmicks'
    Information = 'information'
    #load = 'inviting'
    #load = 'leveling'
    Moderation = 'moderation'
    #load = 'notsafeforwork'
    Other = 'other'

class Methods(Enum):
    load = partial(ShakeBot.load_extension)
    unload = partial(ShakeBot.unload_extension)
    reload = partial(ShakeBot.reload_extension)

async def cogshandler(ctx: ShakeContext, extensions: list[ValidCog], method: Methods) -> None:

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

        ext = f'`{extension}`'
        name = f'` {i}. ` {ext}'
        if error:
            failures += 1
            value = '> ❌ {}'.format(error.replace(extension, ext))
        else:
            value = f'> ☑️ {method.name.lower().capitalize()}ed'
        embed.add_field(name=name, value=value)

    embed.description=f"**{len(extensions) - failures} / {len(extensions)} extensions successfully {method.name.lower()}ed.**"
    return embed