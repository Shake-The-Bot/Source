############
#
from importlib import reload

from discord import Member, Message
from discord.ext.commands import Cog

from Classes import ShakeBot, Testing

from . import message as _message
from . import testing


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
        if message.author.bot:
            return
        if not message.guild:
            return

        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [message.channel, message.guild, message.author]
        )
        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
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
