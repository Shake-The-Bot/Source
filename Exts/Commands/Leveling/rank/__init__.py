############
#
from discord import PartialEmoji, Member
from importlib import reload
from . import rank, testing
from Classes import _, locale_doc, setlocale, ShakeContext, ShakeBot, Testing
from discord.ext.commands import Greedy, Cog, hybrid_command, guild_only
########
#
class rank_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

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

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else rank

        try:    
            await do.command(ctx=ctx, member=member or [ctx.author]).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot): 
    await bot.add_cog(rank_extension(bot))
#
############