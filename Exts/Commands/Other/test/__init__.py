############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeBot, ShakeContext, extras, _, locale_doc, setlocale
from . import test
from discord.ext.commands import hybrid_command, guild_only, is_owner, Cog
########
#
class test_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot
    
    def category(self) -> str: 
        return "other"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{HEAVY PLUS SIGN}')
    
    @hybrid_command(name="test")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def test(self, ctx: ShakeContext):
        _(
            """Test temporary commands"""
        )
        if self.bot.dev:
            reload(test)
        return await test.command(ctx).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(test_extension(bot))
#
############