############
#
from importlib import reload

from discord import RawReactionActionEvent
from discord.ext.commands import Cog

from Classes import ShakeBot, Testing

from . import raw_reaction_add, testing


########
#
class on_raw_reaction_add(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(raw_reaction_add)
        except:
            pass

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if (not payload.guild_id) or payload.member.bot:
            return None

        test = any(
            x in set(self.bot.testing.keys())
            for x in [payload.channel_id, payload.guild_id, payload.user_id]
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                test = False
        do = testing if test else raw_reaction_add

        try:
            await do.Event(bot=self.bot, payload=payload).__await__()

        except:
            if test:
                raise Testing
            raise


# async def setup(bot: ShakeBot):
#     await bot.add_cog(on_raw_reaction_add(bot))


#
############
