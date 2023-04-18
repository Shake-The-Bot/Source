############
#
from discord import PartialEmoji
from importlib import reload
from . import wwyd, testing
from discord.ext.commands import Cog, guild_only, hybrid_command
from Classes import ShakeBot, ShakeContext, setlocale, Testing, _, locale_doc
########
#
class wwyd_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "gimmicks"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(animated=True, name='shakeloading', id=1092832911163654245)

    @hybrid_command(name="wwyd")
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def wwyd(self, ctx: ShakeContext) -> None:
        _(
            """What would you do in this situation."""
        )

        if ctx.testing:
            reload(testing)
            
        do = testing if ctx.testing else wwyd

        try:    
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(wwyd_extension(bot))
#
############