############
#
from discord import PartialEmoji
from importlib import reload
from . import freegames, testing
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext, Testing, extras
from typing import Literal
from discord.ext.commands import Cog, hybrid_group, guild_only, has_permissions
from discord.ext.commands import Greedy
########
#
class freegames_commands_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        try:
            reload(freegames)
        except:
            pass

    def category(self) -> str: 
        return "functions"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GEAR}')

    @hybrid_group(name="freegames")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def freegames(self, ctx: ShakeContext) -> None:
        _(
            """Manage the aboveme features of Shake"""
        )
        pass

    @freegames.command(name="setup")
    @extras(permissions=True)
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def setup(self, ctx: ShakeContext, stores: Greedy[Literal['steam', 'epicgames', 'gog']]) -> None:
        _(
            """Set up the Aboveme-Game with a wizard in seconds.
            
            Parameters
            -----------
            stores: Literal['steam', 'epicgames', 'gog']
                the stores which the channel should support
            """
        )
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False
        do = testing if ctx.testing else freegames

        try:
            await do.command(ctx=ctx, stores=stores).setup()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(freegames_commands_extension(bot))
#
############