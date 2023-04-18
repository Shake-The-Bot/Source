############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeContext, ShakeBot, _, locale_doc, setlocale, extras, Testing
from . import list, testing
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class list_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{SPIRAL NOTE PAD}')
    
    def category(self) -> str: 
        return "information"
    
    @hybrid_command(name='list')
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def list(self, ctx: ShakeContext):
        _(
            """list all guilds"""
        )
        
        if ctx.testing:
            reload(testing)

        do = testing if ctx.testing else list

        try:
            await do.command(ctx=ctx).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise
         
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(list_extension(bot))
#
############