############
#
from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _


########
#
class Games(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot
        self.category_description = _("""Commands for the the Games I offer""")

    @staticmethod
    def category_emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @staticmethod
    def label() -> str:
        return _("Games")

    @staticmethod
    def category_title() -> str:
        return f"{Games.category_emoji}︱{Games.label}"

    @staticmethod
    def describe() -> bool:
        return False


#
############
