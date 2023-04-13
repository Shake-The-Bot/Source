from __future__ import annotations
from importlib import reload
from typing import Optional, Callable, TYPE_CHECKING
from discord import Message, utils, RawBulkMessageDeleteEvent, RawMessageDeleteEvent
from discord.ext import commands
from . import do
from Classes import ShakeContext, event_check

if TYPE_CHECKING:
    from Classes import ShakeBot


def message_getter(message_id: int) -> Callable[[ShakeContext], Optional[Message]]:
    def inner(context: ShakeContext) -> Optional[Message]:
        return context.get_message(message_id)
    return inner

def is_message_older_context(bot: ShakeBot, message_id: int) -> bool:
    if not (cached_context := bot.cached_context): return False
    return message_id < cached_context[0].message.id

def is_command_message():
    def inner(self, payload):
        bot = self.bot
        if is_message_older_context(bot, payload.message_id): 
            return False
        return utils.get(bot.cached_context, message__id=payload.message_id) is not None
    return event_check(inner)

def is_message_context():
    async def inner(self, payload):
        bot = self.bot
        if is_message_older_context(bot, payload.message_id): return False
        return utils.find(message_getter(payload.message_id), bot.cached_context)
    return event_check(inner)

class on_context_update(commands.Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.cooldown_report = commands.CooldownMapping.from_cooldown(5, 30, commands.BucketType.user)

    @commands.Cog.listener('on_raw_bulk_message_delete')
    async def remove_context_messages(self, payload: RawBulkMessageDeleteEvent):
        if self.bot.dev:
            reload(do)
        await do.remove_context_messages_event(bot=self.bot, payload=payload).__await__()

    @commands.Cog.listener('on_raw_message_delete')
    @is_message_context()
    async def remove_context_message(self, payload: RawMessageDeleteEvent):
        if self.bot.dev:
            reload(do)
        await do.remove_context_message_event(bot=self.bot, payload=payload).__await__()

    @commands.Cog.listener('on_raw_message_delete')
    @is_command_message()
    async def on_command_delete(self, payload: RawMessageDeleteEvent):
        if self.bot.dev:
            reload(do)
        await do.on_command_delete_event(bot=self.bot, payload=payload).__await__()


async def setup(bot: ShakeBot) -> None:
    await bot.add_cog(on_context_update(bot))