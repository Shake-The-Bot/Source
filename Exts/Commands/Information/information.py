############
#
from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _


########
#
class Information(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot

    @property
    def description(self) -> str:
        return _(
            """Informative commands about a wide variety of things.
            Sometimes you find out new things 🤷"""
        )

    @staticmethod
    def emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{INFORMATION SOURCE}")

    @property
    def title(self) -> str:
        return f"{Information.emoji}︱{Information.label}"

    @property
    def label(self) -> str:
        return _("Information")

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Information(bot))


#
############
