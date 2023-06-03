from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _

############
#


class Other(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot

    @property
    def description(self) -> str:
        return _("""Other commands without categories""")

    @staticmethod
    def emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{GLOBE WITH MERIDIANS}")

    @property
    def label(self) -> str:
        return _("Other")

    @property
    def title(self) -> str:
        return f"{Other.emoji}︱{Other.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Other(bot))


#
############
