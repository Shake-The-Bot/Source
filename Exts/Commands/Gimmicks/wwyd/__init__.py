############
#
from discord import PartialEmoji
from importlib import reload
from . import wwyd
from Classes.i18n import _, locale_doc
from discord.ext.commands import Cog, guild_only, hybrid_command
from Classes import ShakeBot, ShakeContext, setlocale
########
#
class wwyd_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "gimmicks"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(animated=True, name='shakeloading', id=1092832911163654245))

    @hybrid_command(name="wwyd")
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def wwyd(self, ctx: ShakeContext) -> None:
        _(
            """What would you do in this situation."""
        )
        if self.bot.dev:
            reload(wwyd)
        await wwyd.command(ctx=ctx).__await__()
        return
    
async def setup(bot): 
    await bot.add_cog(wwyd_extension(bot))
#
############