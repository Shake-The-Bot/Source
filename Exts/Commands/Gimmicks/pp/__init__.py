############
#
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import pp
from Classes.i18n import _, locale_doc, setlocale
from discord import app_commands
from discord.ext import commands
########
#
class pp_extension(commands.Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{VIDEO GAME}'))

    def category(self) -> str: 
        return "gimmicks"
    
    @commands.hybrid_command(name="pp")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def pp(self, ctx: ShakeContext, member: commands.Greedy[Member]=None):
        _(
            """Reveal the length of a user's pp

            With this command you can find out, using a very clever and definitely not random generator,
            how long the pp of a selected user is.
            
            __Please note__: If you don't specify a user, I might reveal your pp as well.

            Parameters
            -----------
            member: Greedy[Member]
                the member to ban"""
        )
        if self.bot.dev:
            reload(pp)
        return await pp.command(ctx=ctx, member=member or [ctx.author]).__await__()
########
#
async def setup(bot: ShakeBot): 
    await bot.add_cog(pp_extension(bot))
#
############