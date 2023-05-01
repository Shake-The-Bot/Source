############
#
from typing import Any, TYPE_CHECKING
from traceback import format_exception
import sys
from Classes import _

if TYPE_CHECKING:
    from bot import ShakeBot
else:
    from discord.ext.commands import bot as ShakeBot

#self.bot.log.exception('Ignoring exception in %s', self.event, *self.args, exc_info=True, **self.kwargs)
########
#
class error():
    def __init__(self, bot: ShakeBot, event: str , *args: Any, **kwargs: Any) -> None:
        self.bot: ShakeBot = bot
        self.event: str = event
        self.args: Any = args
        self.kwargs: Any = kwargs
    
    async def __await__(self):
        exc, value, tb, *_ = sys.exc_info()
        dumped = await self.bot.dump(f"{''.join(format_exception(exc, value, tb))}")
        self.bot.log.warning(f"{self.event}: {dumped}")
        return

#
############