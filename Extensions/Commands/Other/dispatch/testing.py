############
#
from ast import literal_eval
from contextlib import suppress

from discord import Forbidden, HTTPException, Message, NotFound

from Classes import ShakeCommand


########
#
class command(ShakeCommand):
    def __init__(self, ctx, event_name, kwargs):
        super().__init__(ctx)
        self.kwargs: Message = kwargs
        self.event_name = event_name

    async def __await__(self):
        kwargs = dict(
            (k, literal_eval(v))
            for k, v in [pair.split("=") for pair in self.kwargs.split()]
        )
        self.bot.dispatch(str(self.event_name), **kwargs)
        with suppress(NotFound, Forbidden, HTTPException):
            await self.ctx.message.add_reaction(self.bot.emojis.hook)


#
############
