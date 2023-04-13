############
#
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import count
from discord.ext import commands
from discord import app_commands, PartialEmoji
from Classes.i18n import _, locale_doc, setlocale
########
#
class count_extension(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{INPUT SYMBOL FOR NUMBERS}'))
    
    def category(self) -> str: 
        return "gimmicks"
    
    @commands.hybrid_command(name='count')
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def count(self, ctx: ShakeContext):
        _(
            """Count for yourself"""
        )
        if self.bot.dev:
            reload(count)
        return await count.command(ctx=ctx).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(count_extension(bot))
#
############