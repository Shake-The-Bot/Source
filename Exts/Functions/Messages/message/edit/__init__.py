############
#
from importlib import reload

from discord import Message
from discord.ext.commands import Cog

from Classes import ShakeBot, Testing, event_check

from . import message_edit, testing


########
#
class on_message_edit(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(message_edit)
        except:
            pass

    @Cog.listener()
    @event_check(
        lambda self, before, after: (before.content and after.content)
        or before.author.bot
    )
    async def on_message_edit(self, before: Message, after: Message):
        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [
                getattr(before, "channel", None),
                getattr(before, "guild", None),
                getattr(before, "author", None),
            ]
            if x is not None
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                test = False
        do = testing if test else message_edit

        try:
            await do.Event(before=before, after=after, bot=self.bot).__await__()

        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_message_edit(bot))


#
############
