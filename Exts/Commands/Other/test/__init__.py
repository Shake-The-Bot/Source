############
#
from discord import PartialEmoji, TextChannel, Guild, User
from discord.app_commands import transformers
from importlib import reload
from typing import Union
from . import test
from Classes import ShakeBot, ShakeContext, extras, _, locale_doc, setlocale, Testing
from discord.ext.commands import hybrid_command, guild_only, is_owner, Cog
########
#
class test_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
    
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
    async def test(self, ctx: ShakeContext, id: str):
        _(
            """Temporarily adds a server/channel/user to the public test build"""
        )

        reload(test)
        try:
            await test.command(ctx, id).__await__()
        except:
            raise Testing

async def setup(bot: ShakeBot): 
    await bot.add_cog(test_extension(bot))
#
############