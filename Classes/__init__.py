############
#
"""
Shake Discord Bot
~~~~~~~~~~~~~~~~~~~~

A basic bot written with a basic wrapper for the Discord API.

"""

from .i18n import (
    Locale, available, locale_doc, 
    _, current_locale, setlocale, default_locale
)
from .helpful import (
    BotBase, ShakeContext, ShakeEmbed, Migration
)
from .checks import (
    event_check, is_beta, has_voted, extras
)
from .useful import (
    captcha, perform_operation, human_join, source_lines, levenshtein, high_level_function, 
    calc, votecheck, votecheck, cogshandler, MISSING, RTFM_PAGE_TYPES
)
from .converter import (
    DurationDelta, ValidArg, ValidKwarg, ValidCog, CleanChannels, Age, Regex
)
from .exceptions import (
    ShakeError, ShakeMissingPermissions, CodeError, NothingHereYet, CheckFailure, 
    NotVoted, GuildNotFound, NotSFW, Testing
)
from bot import ShakeBot


from .tomls.emojis import Emojis
from .tomls.configuration import Config
emojis = Emojis('Assets/utils/emojis.toml')
config = Config('config.toml')

from logging import getLogger, NullHandler
getLogger(__name__).addHandler(NullHandler())

from typing import NamedTuple, Literal
class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal['alpha', 'beta', "candidate", 'final']
    serial: int


__title__ = 'Shake'
__author__ = 'Shake Team'
__license__ = 'MIT'
__copyright__ = '/'
__path__ = __import__('pkgutil').extend_path(__path__, __name__)
__version__: VersionInfo = VersionInfo(major=config.version.major, minor=config.version.minor, micro=config.version.micro, releaselevel=config.version.releaselevel, serial=0)


del getLogger, NullHandler, NamedTuple, Literal, VersionInfo, Config, Emojis
#
############