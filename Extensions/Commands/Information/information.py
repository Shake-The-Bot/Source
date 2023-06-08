############
#
from discord import PartialEmoji

from Classes import Category, ShakeBot, _


########
#
class Information(Category):
    @property
    def description(self) -> str:
        return _(
            """Informative commands about a wide variety of things.
            Sometimes you find out new things 🤷"""
        )

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="ℹ️")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

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
