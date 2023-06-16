############
#
from discord import PartialEmoji

from Classes import Category, ShakeBot, _


########
#
class Features(Category):
    @property
    def description(self) -> str:
        return _("""Commands for the the Features I offer""")

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @property
    def label(self) -> str:
        return _("Features")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Features(bot))


#
############
