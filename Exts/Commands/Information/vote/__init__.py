############
#
from discord import PartialEmoji
from importlib import reload
from . import vote
from Classes import ShakeBot, ShakeContext
from discord.ext.commands import hybrid_command, is_owner, Cog, guild_only
from Classes.checks import extras
from Classes.i18n import _, locale_doc, setlocale
########
#
class vote_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{GEM STONE}'))

    def category(self) -> str: 
        return "information"
    
    @hybrid_command(name='vote')
    @extras(beta=True, owner= True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def vote(self, ctx: ShakeContext):
        _(
            """Get information about Shake+.

            Of course, you dont have to. It's like a tip"""
        )
        if self.bot.dev:
            reload(vote)
        return await vote.vote_command(ctx=ctx).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(vote_extension(bot))
#
############