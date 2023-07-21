from sys import exc_info
from traceback import format_exception
from typing import TYPE_CHECKING, Any

from discord import gateway

from Classes.i18n import _

if TYPE_CHECKING:
    from bot import ShakeBot
else:
    from discord.ext.commands import bot as ShakeBot
############
#


class error:
    def __init__(self, bot: ShakeBot, event: str, *args: Any, **kwargs: Any) -> None:
        self.bot: ShakeBot = bot
        self.event: str = event
        self.args: Any = args
        self.kwargs: Any = kwargs

    async def __await__(self):
        self.bot.log.debug(1)
        exc, value, tb, *_ = exc_info()
        dumped = await self.bot.dump(f"{''.join(format_exception(exc, value, tb))}")
        self.bot.log.warning(f"{self.event}: {dumped}")
        return


#
############
