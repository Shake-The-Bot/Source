############
#
from discord.ext import commands
from discord import PartialEmoji
from Classes.i18n import _
########
#
class leveling(commands.Cog):
    _(
        """Level & Ranking, Voice & Chat"""
    )
    def __init__(self, bot) -> None: 
        self.names = ['leveling']
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{ROCKET}'))

    def long_doc_title(self) -> str: 
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str: 
        return _("Leveling")

    @property
    def help_command_title(self) -> str: 
        return "Level Commands"

async def setup(bot): 
    await bot.add_cog(leveling(bot))
#
############