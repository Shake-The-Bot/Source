############
#
from discord.ext import commands
from discord import PartialEmoji
from Classes import _, ShakeBot
########
#
class leveling(commands.Cog):
    def __init__(self, bot) -> None: 
        self.names = ['leveling']
        self.description = _(
        """Level & Ranking, Voice & Chat"""
        )
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

async def setup(bot: ShakeBot): 
    await bot.add_cog(leveling(bot))
#
############