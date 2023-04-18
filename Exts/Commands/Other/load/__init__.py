############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, _, locale_doc, setlocale, ValidCog, extras, ShakeContext, Testing
from . import load, testing
from discord.ext.commands import Greedy, Cog, hybrid_command, is_owner, guild_only
########
#
class extensions_load_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INBOX TRAY}')

    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name="load")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def load(self, ctx: ShakeContext, *, extension: Greedy[ValidCog]):
        _(
            """Load an extension of the bot
            
            Parameters
            -----------
            extension: Greedy[ValidCog]
                the extension"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else load

        try:    
            await do.command(ctx=ctx, extension=extension).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(extensions_load_extension(bot))
#
############