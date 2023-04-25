############
#
from discord import PartialEmoji
from discord.ext import commands
from Classes.i18n import _
########
#
class gimmicks(commands.Cog):
    def __init__(self, bot) -> None: 
        self.names = [_("gimmicks")]
        self.description = _(
        """Commands for fun and distraction"""
        )
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{VIDEO GAME}')
        #https://discord.com/assets/f1426431eb7c60fb8c072f90acb07ceb.svg

    @property
    def _names(self) -> list[str]:
        return self.names
        
    def long_doc_title(self) -> str: 
        return _("🎮︱Gimmicks")

    @property
    def label(self) -> str: 
        return _("Gimmicks")

    @property
    def help_command_title(self) -> str: 
        return _("Gimmick Commands")

async def setup(bot): 
    await bot.add_cog(gimmicks(bot))
#
############