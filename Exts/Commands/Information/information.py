############
#
from discord.ext import commands
from discord import PartialEmoji
from Classes.i18n import _
########
#
class information(commands.Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot
        self.description = _(
            """Informative commands about a wide variety of things.
            Sometimes you find out new things 🤷"""
        )
        self.names = [_("information"), _("info")]

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INFORMATION SOURCE}')

    def long_doc_title(self) -> str: 
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str: 
        return _("Information")

    @property
    def help_command_title(self) -> str: 
        return _("Information Commands")

async def setup(bot): 
    await bot.add_cog(information(bot))
#
############