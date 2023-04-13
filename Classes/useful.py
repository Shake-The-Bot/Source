from discord.ext.commands import Context
from Classes.exceptions import NotVoted
from discord import File, Interaction
from os import getcwd, listdir, path
from functools import partial
from asyncio import gather
from numpy import zeros
from io import BytesIO
from math import floor
from enum import Enum
from Classes.i18n import _
from Classes.converter import ValidCog
from PIL import ImageFont, ImageDraw, Image
from random import random, choice, randrange
from Classes.secrets.configuration import Config
from dateutil.relativedelta import relativedelta

from typing import (Any, Union, Literal, Optional, Iterator, Sequence, Any, TYPE_CHECKING, _SpecialForm, _type_check)
from discord.ext.commands.errors import (ExtensionNotLoaded, ExtensionAlreadyLoaded, NoEntryPointError, ExtensionNotFound)

if TYPE_CHECKING:
    from bot import ShakeBot
    from Classes.helpful import ShakeEmbed, ShakeContext

else:
    from discord.ext.commands import Bot as ShakeBot, Context as ShakeContext
    from discord import Embed as ShakeEmbed
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


""""    Image    """

async def captcha(bot):
    # creation & text
    image = Image.new("RGBA", (325, 100), color=bot.config.embed.hex_colour)#(0, 0, 255))
    draw = ImageDraw.Draw(image)
    text = ' '.join(choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(5))
    W, H = (325, 100)
    w, h = draw.textsize(text, font=ImageFont.truetype(font="arial.ttf", size=60))
    draw.text(((W - w) / 2, (H - h) / 2), text, font=ImageFont.truetype(font="arial.ttf", size=60), fill='#000000')#(90, 90, 90))    
    filename = 'captcha'+str(choice(range(10)))

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




"""     Text     """

def human_join(seq: Sequence[str], delimiter: str = ', ', final: Literal['or', 'and'] = 'or', joke: bool = False) -> str:
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
            if (child.startswith(".") or child.endswith('.toml') or child in ('LICENSE', 'README.md')): 
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
    with open("POTFILES.in") as f:
        files = f.read().splitlines()

    for file in files:
        with open(f"../{file}", "r+") as f:
            stuff = f.read().splitlines()
            stuff2 = stuff
            done = 0
            for idx, line in enumerate(stuff):
                if "@" in line and (".group" in line or ".command" in line):
                    stuff2.insert(idx + 1, "    @locale_doc")
                    done += 1
            f.seek(0)
            f.write("\n".join(stuff2))
            f.truncate()

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

class Action(Enum):

    LOAD = partial(ShakeBot.load_extension)
    UNLOAD = partial(ShakeBot.unload_extension)
    RELOAD = partial(ShakeBot.reload_extension)

async def cogs_handler(
        ctx: ShakeContext, 
        extensions: ValidCog, 
        method: Literal['load', 'unload', 'reload'] # TODO: update to the Enums above
    ) -> None: 

    async def do_cog(exts: str) -> str:
        func = getattr(ctx.bot, f'{method}_extension')
        try: 
            await func(f'{exts}')
        except ExtensionNotFound:
            return (f'`{exts}`', 'not found')
        except (ExtensionNotLoaded, ExtensionAlreadyLoaded, NoEntryPointError) as e: 
            return (f'`{exts}` {type(e).__name__}', f'{e}')
        return (None, None)
    
    embed = ShakeEmbed(colour=config.embed.colour, description=f"{ctx.bot.emojis.hook}")
    outputs = await gather(*map(do_cog, extensions))
    for name, value in map(tuple, outputs): 
        if any(x is None for x in (name, value)): continue
        embed.add_field(name=name, value=f'```py\n{value}\n```', inline=False)
    await ctx.smart_reply(embed=embed)
    return