############
#
from importlib import reload

from discord import Message
from discord.ext.commands import Cog

from Classes import ShakeBot, Testing, event_check

from . import edit, testing


########
#
class on_message_edit(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(edit)
        except:
            pass

    @Cog.listener()
    @event_check(
        lambda self, before, after: (before.content and after.content)
        or before.author.bot
    )
    async def on_message_edit(self, before: Message, after: Message):
        if not getattr(before, "guild"):
            return

        test = any(
            x.id in set(self.bot.testing.keys())
            for x in filter(
                lambda _: _ is not None,
                (
                    getattr(before, "channel", None),
                    getattr(before, "guild", None),
                    getattr(before, "author", None),
                ),
            )
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                test = False
        do = testing if test else edit

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
