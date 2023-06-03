from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _

############
#


class Moderation(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot
        self.category_description = _(
            """Moderation related commands.
            (Each of these commands requires certain authorization)."""
        )

    @staticmethod
    def category_emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{POLICE OFFICER}")

    @staticmethod
    def label() -> str:
        return _("Moderation")

    @staticmethod
    def category_title() -> str:
        return f"{Moderation.category_emoji}︱{Moderation.label}"

    @staticmethod
    def describe() -> bool:
        return False


#
############
