############
#
from discord import PartialEmoji
from importlib import reload
from . import aboveme, testing
from discord.ext.commands import Cog, hybrid_group, has_permissions, guild_only
from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
########
#
class aboveme_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot
        try:
            reload(aboveme)
        except:
            pass


    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEAR}')

    @hybrid_group(name="aboveme")
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def aboveme(self, ctx: ShakeContext) -> None:
        _(
            """Manage the aboveme features of Shake"""
        )
        pass

    @aboveme.command(name="setup")
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(
        self, ctx: ShakeContext
    ) -> None:
        _(
            """Set up the Aboveme-Game with a wizard in seconds."""
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False

        do = testing if ctx.testing else aboveme

        try:
            await do.command(ctx=ctx).setup()
        except:
            if ctx.testing:
                raise Testing
            raise
    
async def setup(bot: ShakeBot): 
    await bot.add_cog(aboveme_extension(bot))
#
############