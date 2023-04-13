############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeContext, ShakeBot, _, locale_doc, setlocale, extras
from . import list
from discord.ext.commands import Cog, hybrid_command, guild_only, is_owner
########
#
class list_extension(Cog):
    def __init__(self, bot) -> None: self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{SPIRAL NOTE PAD}'))
    
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
        if self.bot.dev:
            reload(list)
        return await list.command(ctx=ctx).__await__()
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(list_extension(bot))
#
############