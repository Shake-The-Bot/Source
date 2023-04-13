############
#
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import ShakeBot
else:
    from discord.ext.commands import bot as ShakeBot
########
#
class error():
    def __init__(self, bot: ShakeBot, event: str , *args: Any, **kwargs: Any) -> None:
        self.bot: ShakeBot = bot
        self.event: str = event
        self.args: Any = args
        self.kwargs: Any = kwargs
    
    async def __await__(self):
        self.bot.log.exception('Ignoring exception in %s', self.event, *self.args, exc_info=True, **self.kwargs)
#
############