############
#
from discord import PartialEmoji
from importlib import reload
from . import aboveme, testing
from discord.ext.commands import Cog, hybrid_group, guild_only, has_permissions
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing, extras
########
#
class oneword_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEAR}')

    @hybrid_group(name="oneword")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def oneword(self, ctx: ShakeContext) -> None:
        _(
            """Manage the oneword features of Shake"""
        )
        pass
    
    @oneword.command(name="setup")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(self, ctx: ShakeContext) -> None:
        _(
            """Set up the Oneword-Game with a wizard in seconds."""
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False

        do = testing if ctx.testing else aboveme
        try:
            await do.command(ctx=ctx).setup()
    
        except:
            if ctx.testing:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(oneword_extension(bot))
#
############