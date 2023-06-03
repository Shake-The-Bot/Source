from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _

############
#


class Gimmicks(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot

    @property
    def description(self) -> str:
        return _("""Commands for fun and distraction""")

    @staticmethod
    def emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @property
    def label(self) -> str:
        return _("Gimmicks")

    @property
    def title(self) -> str:
        return f"{Gimmicks.emoji}︱{Gimmicks.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Gimmicks(bot))


#
############
