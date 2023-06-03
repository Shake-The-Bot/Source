from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _

############
#


class Moderation(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot

    @property
    def description(self) -> str:
        return _(
            """Moderation related commands.
            (Each of these commands requires certain authorization)."""
        )

    @staticmethod
    def emoji() -> PartialEmoji:
        return PartialEmoji(name="\N{POLICE OFFICER}")

    @property
    def label(self) -> str:
        return _("Moderation")

    @property
    def title(self) -> str:
        return f"{Moderation.emoji}︱{Moderation.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Moderation(bot))


#
############
