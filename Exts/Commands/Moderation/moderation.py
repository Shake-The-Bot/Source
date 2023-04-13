############
#
from discord.ext import commands
from discord import PartialEmoji
from Classes.i18n import _
########
#
class moderation(commands.Cog):
    _(
        """Moderation related commands.
        (Each of these commands requires certain authorization)."""
    )
    def __init__(self, bot) -> None: 
        self.names = ['moderation', 'mod']
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{POLICE OFFICER}')

    def long_doc_title(self) -> str: 
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str: 
        return ("Moderation")

    @property
    def help_command_title(self) -> str: 
        return "Moderations Befehle"

async def setup(bot): 
    await bot.add_cog(moderation(bot))
#
############