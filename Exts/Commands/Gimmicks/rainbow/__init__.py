############
#
from typing import Optional
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import rainbow
from discord import app_commands
from Classes.i18n import _, locale_doc, setlocale
from discord.ext import commands
########
#
class rainbow_extension(commands.Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        
    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{RAINBOW}'))

    def category(self) -> str: 
        return "gimmicks"
    
    @commands.hybrid_command(name="rainbow")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def rainbow(self, ctx: ShakeContext, member: Optional[Member]=None):
        _(
            """Show your support to LGBT+ with a rainbow filter! ^^

            Parameters
            -----------
            member: discord.Member
                the member to add"""
        )
        if self.bot.dev:
            reload(rainbow)
        return await rainbow.command(ctx=ctx, member=member or ctx.author,).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(rainbow_extension(bot))
#
############