from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _

############
#


class Other(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot
        self.category_description = _("""Other commands without categories""")

    @staticmethod
    def category_emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{GLOBE WITH MERIDIANS}")

    @staticmethod
    def label() -> str:
        return _("Other")

    @staticmethod
    def category_title() -> str:
        return f"{Other.category_emoji}︱{Other.label}"

    @staticmethod
    def describe() -> bool:
        return False


#
############
