############
#
from discord import PartialEmoji
from discord.ext import commands
from Classes import _, ShakeBot
########
#
class functions(commands.Cog):
    def __init__(self, bot) -> None: 
        self.names = [_("functions")]
        self.description = _(
        """Commands for the functions of mine"""
        )
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='⚙️')
        return PartialEmoji(name='\N{VIDEO GAME}')
        #https://discord.com/assets/f1426431eb7c60fb8c072f90acb07ceb.svg

    @property
    def _names(self) -> list[str]:
        return self.names
        
    def long_doc_title(self) -> str: 
        return _("🧷︱Functions")

    @property
    def describe(self) -> bool:
        return False

    @property
    def label(self) -> str: 
        return _("Functions")

    @property
    def help_command_title(self) -> str: 
        return _("Functions Commands")

async def setup(bot: ShakeBot): 
    await bot.add_cog(functions(bot))
#
############