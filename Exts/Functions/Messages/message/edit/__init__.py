############
#
from discord import Message
from importlib import reload
from Classes import event_check
from . import do
from discord.ext import commands
########
#
class on_message_edit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    @event_check(lambda self, before, after:  (before.content and after.content) or before.author.bot)
    async def on_message_edit(self, before: Message, after: Message):
        if self.bot.dev:
            reload(do)
        return await do.message_edit_event(before=before, after=after, bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_message_edit(bot))
#
############