"""
Shake Discord Bot
~~~~~~~~~~~~~~~~~~~~

A basic bot written with a basic wrapper for the Discord API.

"""

from typing import Literal, NamedTuple

from bot import ShakeBot

from .converter import *
from .decorator import *
from .exceptions import *
from .helpful import *
from .i18n import *
from .logging import *
from .necessary import *
from .tomls import *
from .types import *
from .useful import *

############
#


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int

    def __str__(self) -> str:
        return "{}.{}.{}".format(self.major, self.minor, self.micro)


__title__ = "Shake"
__author__ = "Shake Team"
__license__ = "MIT"
__copyright__ = "/"
__version__: VersionInfo = VersionInfo(
    major=config.bot.version.major,
    minor=config.bot.version.minor,
    micro=config.bot.version.micro,
    releaselevel=config.bot.version.releaselevel,
    serial=0,
)

#
############
del NamedTuple, Literal, VersionInfo
