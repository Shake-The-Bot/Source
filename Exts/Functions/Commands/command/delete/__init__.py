from __future__ import annotations
from importlib import reload
from typing import Optional, Callable, TYPE_CHECKING
from discord import Message, utils, RawBulkMessageDeleteEvent, RawMessageDeleteEvent
from discord.ext.commands import Cog, CooldownMapping, BucketType
from . import delete, testing
from Classes import ShakeContext, event_check, Testing

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

class on_context_update(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.cooldown_report = CooldownMapping.from_cooldown(5, 30, BucketType.user)

    @Cog.listener('on_raw_bulk_message_delete')
    async def remove_context_messages(self, payload: RawBulkMessageDeleteEvent):
        
        test = any(x in list(self.bot.tests.keys()) for x in (payload.channel_id, payload.guild_id))
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else delete

        try:
            await do.event(bot=self.bot, payload=payload, event='remove_context_messages').__await__()
    
        except:
            if test:
                raise Testing
            raise

    @Cog.listener('on_raw_message_delete')
    @is_message_context()
    async def remove_context_message(self, payload: RawMessageDeleteEvent):
        test = any(x in list(self.bot.tests.keys()) for x in (payload.channel_id, payload.guild_id))
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else delete

        try:
            await do.event(bot=self.bot, payload=payload, event='remove_context_message').__await__()
    
        except:
            if test:
                raise Testing
            raise

    @Cog.listener('on_raw_message_delete')
    @is_command_message()
    async def on_command_delete(self, payload: RawMessageDeleteEvent):
        test = any(x in list(self.bot.tests.keys()) for x in (payload.channel_id, payload.guild_id))
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else delete

        try:
            await do.event(bot=self.bot, payload=payload, event='on_command_delete').__await__()
    
        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot) -> None:
    await bot.add_cog(on_context_update(bot))