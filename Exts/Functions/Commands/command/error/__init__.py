############
#
from importlib import reload

from . import do
from typing import Union
from discord.ext import commands
from Classes import ShakeContext, ShakeBot
from discord import Interaction
########
#
class on_command_error(commands.Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Union[ShakeContext, Interaction], error: commands.CommandError):
        if isinstance(ctx, ShakeContext) and ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return
        if self.bot.dev:
            reload(do)
        return await do.command_error_event(ctx=ctx, error=error).__await__()

async def setup(bot): 
    await bot.add_cog(on_command_error(bot))
#
############