############
#
from ast import literal_eval
from contextlib import suppress
from discord import Message, Forbidden, HTTPException
from Classes import ShakeContext, ShakeBot
########
#
class command():
    def __init__(self, ctx: ShakeContext, event_name, kwargs):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.kwargs: Message = kwargs
        self.event_name = event_name

    async def __await__(self):
        kwargs = dict((k, literal_eval(v)) for k, v in [pair.split('=') for pair in self.kwargs.split()])
        self.bot.dispatch(str(self.event_name), **kwargs)
        with suppress(Forbidden, HTTPException):
            await self.ctx.message.add_reaction(self.bot.emojis.hook)

#
############