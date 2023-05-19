############
#
from discord.ext import commands
from discord import PartialEmoji
from Classes.i18n import _
########
#
class inviting(commands.Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot
        self.description = _(
        """Useful Commands to track invites and and get some members with these"""
        )
        self.names = [_("information"), _("info")]

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INCOMING ENVELOPE}')

    def long_doc_title(self) -> str: 
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str: 
        return _("Inviting")

    @property
    def describe(self) -> bool:
        return False

    @property
    def help_command_title(self) -> str: 
        return "invite Befehle"

async def setup(bot): 
    await bot.add_cog(inviting(bot))
#
############