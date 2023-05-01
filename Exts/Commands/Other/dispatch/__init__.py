############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras, Testing
from . import dispatch, testing
from typing import Optional
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class dispatch_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(dispatch)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{PISTOL}')
    
    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name="dispatch")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def dispatch(self, ctx: ShakeContext, event: Optional[str], kwargs):
        _(
            """Send an event

            Parameters
            -----------
            event: Optional[str]
                the name of the event

            kwargs: Any
                event keyword arguments"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else dispatch

        try:    
            await do.command(ctx, event, kwargs).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot): 
    await bot.add_cog(dispatch_extension(bot))
#
############