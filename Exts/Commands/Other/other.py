############
#
from discord import PartialEmoji
from discord.ext import commands
from Classes import _, ShakeBot
########
#
#@locale_doc
class other(commands.Cog):
    def __init__(self, bot) -> None:
        self.names = ['other', 'other', 'others']
        self.description = _(
            """Other commands without categories"""
        )
        self.bot = bot
        
    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{GLOBE WITH MERIDIANS}')

    
    def long_doc_title(self) -> str: 
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str: 
        return _("Other")

    @property
    def describe(self) -> bool:
        return False
    
    @property
    def help_command_title(self) -> str: 
        return _("Other Commands")

async def setup(bot: ShakeBot): 
    await bot.add_cog(other(bot))
#
############