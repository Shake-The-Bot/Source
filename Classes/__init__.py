"""
Shake Discord Bot
~~~~~~~~~~~~~~~~~~~~

A basic bot written with a basic wrapper for the Discord API.

"""

from typing import Literal, NamedTuple

from bot import ShakeBot

from .converter import *
from .decorator import *
from .decorator import locale_doc, setlocale
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
    major=config.version.major,
    minor=config.version.minor,
    micro=config.version.micro,
    releaselevel=config.version.releaselevel,
    serial=0,
)

#
############
del NamedTuple, Literal, VersionInfo
