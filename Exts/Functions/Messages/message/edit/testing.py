############
#
from discord import Message, utils
from Classes import ShakeBot, ShakeContext
########
#
class event():
    def __init__(self, before: Message, after: Message, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.after = after
        self.before = before
    
    async def __await__(self):
        if not self.before.embeds and not self.after.embeds:
            if self.before.clean_content.strip() == self.after.clean_content.strip():
                return
            context: ShakeContext = utils.find(lambda ctx: ctx.message == self.after, self.bot.cached_context)
            if context:
                await context.reinvoke(message=self.after)
            else: 
                await self.bot.process_commands(self.after)
#
############