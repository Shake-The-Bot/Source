############
#
from discord import Message
from importlib import reload
from Classes import Testing, ShakeBot
from . import message as _message, testing
from discord.ext.commands import Cog
########
#
class on_message(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(_message)
        except:
            pass

    @Cog.listener()
    async def on_message(self, message: Message):
        await self.bot.wait_until_ready()

        if message.author.bot: 
            return
        test = any(x.id in set(self.bot.cache['testing'].keys()) for x in [message.channel, message.guild, message.author])
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                test = False
        do = testing if test else _message

        try:
            await do.Event(message=message, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_message(bot))
#
############