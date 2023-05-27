#from discord.ext.commands.errors import *
from typing import List, Any, Optional
from discord.ext.commands.errors import (
    GuildNotFound as _GuildNotFound, CommandError, BotMissingPermissions,
    CheckFailure, ChannelNotFound as _ChannelNotFound
)

__all__ = (
    'ShakeError', 'ShakeMissingPermissions', 'CodeError', 'NothingHereYet', 'CheckFailure', 
    'NotVoted', 'GuildNotFound', 'NotSFW', 'Testing'
)

class ShakeError(CommandError):
    """Displays error in embed without generating signature hint"""
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message=message)
        self.message = message

class Testing(CommandError):
    """Displays error in embed without generating signature hint"""
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message=message)
        self.message = message

class NotSFW(CommandError):
    def __init__(self, *args: Any) -> None:
        self.message = "This Content is not Safe For Work and will not be shown."
        super().__init__(self.message, *args)

class ShakeMissingPermissions(BotMissingPermissions):
    def __init__(self, missing_permissions: List[str], message: Optional[str] = None, *args: Any) -> None:
        super().__init__(missing_permissions, *args)
        self.message = message

class CodeError(Exception):
    """ Something totaly went wrong """

class NothingHereYet(CommandError):
    """ Something not Implemented??"""

class GuildNotFound(_GuildNotFound):
    """Exception thrown when the Guild object could not be found 
    by converters such as GuildConverter because 
    the bot does not have access to it or it does not exist.
    This inherits from :exc:`CommandError`."""
    def __init__(self, argument: str, message: Optional[str] = None) -> None:
        super().__init__(argument)
        self.message = message
    pass

class ChannelNotFound(_ChannelNotFound):
    """Exception thrown when the Channel object could not be found 
    by converters such as TextChannelConverter because 
    the bot does not have access to it or it does not exist.
    This inherits from :exc:`CommandError`."""
    def __init__(self, argument: str, message: Optional[str] = None) -> None:
        super().__init__(argument)
        self.message = message
    pass

class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`.Command.checks` have failed.
    This inherits from :exc:`CommandError`"""
    pass

class NotVoted(CheckFailure):
    """I think it speaks for itself"""
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message, *args)

class NoDumpingSpots(Exception):
    """Raised when all Dump Hosts returned nothing"""
    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(m=message)