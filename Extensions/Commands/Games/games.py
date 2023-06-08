############
#
from discord import PartialEmoji

from Classes import Category, ShakeBot, _


########
#
class Games(Category):
    @property
    def description(self) -> str:
        return _("""Commands for the the Games I offer""")

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @property
    def label(self) -> str:
        return _("Games")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Games(bot))


#
############
