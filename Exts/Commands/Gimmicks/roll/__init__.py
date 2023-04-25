############
#
from typing import Optional
from . import roll, testing
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
from discord.ext.commands import Cog, hybrid_command, guild_only
########
#
class roll_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(roll)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GAME DIE}')

    def category(self) -> str: 
        return "gimmicks"

    @hybrid_command(name="roll")
    @guild_only()
    @setlocale()
    @locale_doc
    async def roll(self, ctx: ShakeContext, start: Optional[int] = 1, end: Optional[int] = 6):
        _(
            """Displays a random number in a specified range of values. (Default: 1-6)

            Parameters
            -----------
            start: Optional[int]
                the start to roll at

            end: Optional[int]
                the endlimit to roll till"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False

        do = testing if ctx.testing else roll
        try:    
            await do.command(ctx=ctx, start=start or 5, end=end or 6).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(roll_extension(bot))
#
############