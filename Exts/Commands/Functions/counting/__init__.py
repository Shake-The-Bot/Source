############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional
from . import counting, testing
from discord.ext.commands import hybrid_group, has_permissions, Cog, guild_only
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
########
#
class counting_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEAR}')

    @hybrid_group(name="counting")
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def counting(self, ctx: ShakeContext) -> None:
        _(
            """Manage the counting features of Shake"""
        )
        pass

    
    @counting.command(name="setup")
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(
        self, ctx: ShakeContext, hardcore: Optional[bool] = False, numbersonly: Optional[bool] = None, goal: Optional[int] = False) -> None:
        _(
            """Set up Counting with a wizard in seconds.

            Parameters
            -----------
            hardcore: Optional[bool]
                if hardcore

            numbersonly: Optional[bool]
                if numbersonly

            goal: Optional[int]
                the goal
            """
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
            
        do = testing if ctx.testing else counting

        try:
            await do.command(ctx=ctx, hardcore=hardcore, numbersonly=numbersonly, goal=goal).setup()
        except:
            if ctx.testing:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(counting_extension(bot))
#
############