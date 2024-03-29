############
#
from importlib import reload

from discord.ext.commands import Cog

from Classes import ShakeBot, ShakeContext, Testing

from . import command_completion, testing


########
#
class on_command_completion(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bot.cache.setdefault("used_commands", {})
        try:
            reload(command_completion)
        except:
            pass

    @Cog.listener()
    async def on_command_completion(self, ctx: ShakeContext):
        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [ctx.author, ctx.guild, ctx.channel]
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if test else command_completion

        try:
            await do.Event(ctx=ctx, bot=self.bot).__await__()

        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_command_completion(bot))


#
############
