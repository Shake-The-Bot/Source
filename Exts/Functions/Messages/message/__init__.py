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

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot: 
            return
        test = any(x.id in list(self.bot.tests.keys()) for x in (message.channel, message.guild, message.author))
        
        if test:
            reload(testing)
        do = testing if test else _message

        try:
            await do.event(message=message, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_message(bot))
#
############