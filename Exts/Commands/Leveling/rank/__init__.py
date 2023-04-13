############
#
from discord import PartialEmoji, Member
from importlib import reload

from Classes import ShakeContext
from . import do
from Classes.i18n import _, locale_doc, setlocale
from discord.ext.commands import Greedy, Cog, hybrid_command, guild_only
########
#
class rank_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name="\N{ROCKET}")
    
    def category(self) -> str: 
        return "leveling"

    @hybrid_command(name="rank", alias=['level', 'xp'])
    @guild_only()
    @setlocale()
    @locale_doc
    async def rank(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """get your current level status

            Parameters
            -----------
            member: Greedy[discord.Member]
                the member to get the level information about
                """
        )
        if self.bot.dev:
            reload(do)
        return await do.rank_command(ctx=ctx, member=member or [ctx.author]).__await__()

async def setup(bot): 
    await bot.add_cog(rank_extension(bot))
#
############