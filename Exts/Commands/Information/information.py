############
#
from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _


########
#
class Information(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot
        self.category_description = _(
            """Informative commands about a wide variety of things.
            Sometimes you find out new things 🤷"""
        )
        self.names = [_("information"), _("info")]

    @property
    def category_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INFORMATION SOURCE}")

    @property
    def category_title(self) -> str:
        return f"{self.display_emoji}︱{self.label}"

    @property
    def category_label(self) -> str:
        return _("Information Commands")

    @property
    def describe(self) -> bool:
        return False


#
############
