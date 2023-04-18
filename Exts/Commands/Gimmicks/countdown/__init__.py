############
#
from importlib import reload
from . import countdown, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
from discord import PartialEmoji
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
########
#
class countdown_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INPUT SYMBOL FOR NUMBERS}')
    
    def category(self) -> str: 
        return 'gimmicks'
    
    @hybrid_command(name='countdown')
    @guild_only()
    @setlocale()
    @locale_doc
    async def countdown(self, ctx: ShakeContext):
        _(
            """It's the final countdown"""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else countdown

        try:    
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(countdown_extension(bot))
#
############