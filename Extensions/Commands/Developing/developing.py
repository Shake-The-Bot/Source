############
#
from discord import PartialEmoji

from Classes import Category, ShakeBot, _


########
#
class Developing(Category):
    @property
    def description(self) -> str:
        return _(
            """Dev commands to configure/set a lot of things of the bot.
            Sometimes you have to list them as Dev 🤷."""
        )

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="settings", id=1130987101723316234)

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def label(self) -> str:
        return _("Developing")

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Developing(bot))


#
############
