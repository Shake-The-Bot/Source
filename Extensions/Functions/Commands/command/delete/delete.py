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
    def inner(context: ShakeContext) -> Optional[Message]: 
        if isinstance(context, ShakeContext):
            return context.get(message_id)
    return inner


def is_message_older_context(bot: ShakeBot, message_id: int) -> bool:
    if not (context := bot.cache['context']): return False
    return message_id < context[0].message.id

class Event():
    def __init__(self, bot: ShakeBot, payload: RawBulkMessageDeleteEvent, event: Literal['remove_context_messages', 'remove_context_message', 'on_command_delete_event']):
        self.bot: ShakeBot = bot
        self.payload = payload
        self.event = event

    async def __await__(self):
        if self.event == 'remove_context_messages':
            for message_id in self.payload.message_ids:
                if is_message_older_context(self.bot, message_id): continue
                context: Optional[ShakeContext] = utils.find(message_getter(message_id), self.bot.cache['context'])
                if context: 
                    context.pop(message_id)

        elif self.event == 'remove_context_message':
            target = self.payload.message_id
            context: Optional[ShakeContext] = utils.find(message_getter(target), self.bot.cache['context'])
            if context:
                context.pop(target)
        
        elif self.event == 'on_command_delete':
            context: ShakeContext = utils.get(self.bot.cache['context'], message__id=self.payload.message_id)
            await context.delete_all()

#
########