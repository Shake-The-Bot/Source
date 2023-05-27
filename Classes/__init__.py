"""
Shake Discord Bot
~~~~~~~~~~~~~~~~~~~~

A basic bot written with a basic wrapper for the Discord API.

"""

from typing import NamedTuple, Literal

from .i18n import *
from .database import *
from .logging import *
from .helpful import *
from .checks import *
from .useful import *
from .converter import *
from .exceptions import *
from .tomls import *
from bot import ShakeBot
############
#

emojis = Emojis('Assets/utils/emojis.toml')
config = Config('config.toml')

class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal['alpha', 'beta', "candidate", 'final']
    serial: int

    def __str__(self) -> str:
        return '{}.{}.{}@{}.{}'.format(self.major, self.minor, self.micro, self.releaselevel, self.serial)

__title__ = 'Shake'
__author__ = 'Shake Team'
__license__ = 'MIT'
__copyright__ = '/'
__version__: VersionInfo = VersionInfo(major=config.version.major, minor=config.version.minor, micro=config.version.micro, releaselevel=config.version.releaselevel, serial=0)

#
############
del NamedTuple, Literal, VersionInfo, Config, Emojis