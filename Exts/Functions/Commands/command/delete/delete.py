############
#
from __future__ import annotations
from typing import Optional, Callable, TYPE_CHECKING, Literal, Union
from discord import Message, RawBulkMessageDeleteEvent, RawBulkMessageDeleteEvent, utils
from Classes import ShakeContext

if TYPE_CHECKING: 
    from Classes import ShakeBot
########
#

def message_getter(message_id: int) -> Callable[[ShakeContext], Optional[Message]]:
    def inner(context: ShakeContext) -> Optional[Message]: return context.get_message(message_id)
    return inner


def is_message_older_context(bot: ShakeBot, message_id: int) -> bool:
    if not (cached_context := bot.cached_context): return False
    return message_id < cached_context[0].message.id

class event():
    def __init__(self, bot: ShakeBot, payload: RawBulkMessageDeleteEvent, event: Literal['remove_context_messages', 'remove_context_message', 'on_command_delete_event']):
        self.bot: ShakeBot = bot
        self.payload = payload
        self.event = event

    async def __await__(self):
        if self.event == 'remove_context_messages':
            for message_id in self.payload.message_ids:
                if is_message_older_context(self.bot, message_id): continue
                if ctx := utils.find(message_getter(message_id), self.bot.cached_context): ctx.remove_message(message_id)

        elif self.event == 'remove_context_message':
            target = self.payload.message_id
            if ctx := utils.find(message_getter(target), self.bot.cached_context):
                ctx.remove_message(target)
        
        elif self.event == 'on_command_delete':
            context = utils.get(self.bot.cached_context, message__id=self.payload.message_id)
            await context.delete_all()

#
########