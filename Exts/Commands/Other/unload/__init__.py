############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeContext, ShakeBot, ValidCog, _, locale_doc, setlocale, extras
from . import unload
from discord.ext.commands import Greedy, Cog, hybrid_command, guild_only, is_owner

########
#
class extensions_unload_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{OUTBOX TRAY}'))

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
        if self.bot.dev:
            reload(unload)
        return await unload.unload_command(ctx=ctx, extension=extension).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(extensions_unload_extension(bot))
#
############