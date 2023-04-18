############
#
from discord import Message
from importlib import reload
from Classes import event_check, Testing, ShakeBot
from . import message_edit, testing
from discord.ext.commands import Cog
########
#
class on_message_edit(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    @event_check(lambda self, before, after:  (before.content and after.content) or before.author.bot)
    async def on_message_edit(self, before: Message, after: Message):
        test = any(x.id in list(self.bot.tests.keys()) for x in (getattr(before, 'channel', None), getattr(before, 'guild', None), getattr(before, 'author', None)) if x is not None)
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else message_edit

        try:
            await do.event(before=before, after=after, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_message_edit(bot))
#
############