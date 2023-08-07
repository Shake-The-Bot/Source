from typing import Any, Optional

from discord.ext.commands.errors import CheckFailure, CommandError

__all__ = (
    "ShakeError",
    "CodeError",
    "Testing",
    "NotSFW",
    "CheckFailure",
    "NotVoted",
    "NoDumpingSpots",
)


class ShakeError(CommandError):
    """Displays error in embed without generating signature hint"""

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message=message)
        self.message = message


class CodeError(Exception):
    """Something totaly went wrong"""


class Testing(CommandError):
    """Displays error in embed without generating signature hint"""

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message=message)
        self.message = message


class NotSFW(CommandError):
    def __init__(self, *args: Any) -> None:
        self.message = "This Content is not Safe For Work and will not be shown."
        super().__init__(self.message, *args)


class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`.Command.checks` have failed.
    This inherits from :exc:`CommandError`"""

    pass


class NotVoted(CheckFailure):
    """I think it speaks for itself"""

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message, *args)


class NoDumpingSpots(CommandError):
    """Raised when all Dump Hosts returned nothing"""

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        super().__init__(message)
