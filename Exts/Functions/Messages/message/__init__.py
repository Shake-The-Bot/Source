############
#
from discord import Message
from importlib import reload
from . import do
from discord.ext import commands
########
#
class on_message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot: 
            return
        if self.bot.dev:
            reload(do) 
        await do.message_event(message=message, bot=self.bot).__await__()
        return
    
async def setup(bot): 
    await bot.add_cog(on_message(bot))
#
############