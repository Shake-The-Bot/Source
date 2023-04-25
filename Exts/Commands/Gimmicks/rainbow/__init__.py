############
#
from typing import Optional
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
from . import rainbow, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
########
#
class rainbow_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        try:
            reload(rainbow)
        except:
            pass
        
    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{RAINBOW}')

    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name="rainbow")
    @guild_only()
    @setlocale()
    @locale_doc
    async def rainbow(self, ctx: ShakeContext, member: Optional[Member]=None):
        _(
            """Show your support to LGBT+ with a rainbow filter! ^^

            Parameters
            -----------
            member: discord.Member
                the member to add"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False
        do = testing if ctx.testing else rainbow

        try:    
            await do.command(ctx=ctx, member=member or ctx.author,).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(rainbow_extension(bot))
#
############