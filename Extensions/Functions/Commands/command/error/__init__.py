############
#
from importlib import reload

from discord import Interaction
from discord.ext.commands import Cog, CommandError

from Classes import ShakeBot, ShakeContext

from . import command_error, testing


########
#
class on_command_error(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(command_error)
        except:
            pass

    @Cog.listener()
    async def on_command_error(
        self, ctx: ShakeContext | Interaction, error: CommandError
    ):
        if (
            isinstance(ctx, ShakeContext)
            and ctx.cog
            and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None
        ):
            return

        author: ShakeBot = ctx.author if isinstance(ctx, ShakeContext) else ctx.user
        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [author, ctx.guild, ctx.channel]
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                test = False
        do = testing if test else command_error

        try:
            await do.Event(ctx=ctx, error=error).__await__()

        except:
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_command_error(bot))


#
############
