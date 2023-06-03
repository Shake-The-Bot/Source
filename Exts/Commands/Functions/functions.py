############
#
from discord import PartialEmoji
from discord.ext import commands

from Classes import ShakeBot, _


########
#
class Functions(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot = bot
        self.category_description = _("""Commands for the functions of mine""")

    @property
    def category_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @property
    def label(self) -> str:
        return _("Functions")

    @property
    def category_title(self) -> str:
        return f"{self.category_emoji}︱{self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Functions(bot))


#
############
