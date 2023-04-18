############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeContext, ShakeBot, ValidCog, _, locale_doc, setlocale, extras, Testing
from . import unload, testing
from discord.ext.commands import Greedy, Cog, hybrid_command, guild_only, is_owner

########
#
class extensions_unload_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{OUTBOX TRAY}')

    def category(self) -> str: 
        return 'other'
    
    @hybrid_command(name="unload")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def unload(self, ctx: ShakeContext, *, extension: Greedy[ValidCog]):
        _(
            """Unload extensions of the bot

            Parameters
            -----------
            extension: Greedy[ValidCog]
                the extension"""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else unload

        try:
            await do.command(ctx=ctx, extension=extension).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(extensions_unload_extension(bot))
#
############