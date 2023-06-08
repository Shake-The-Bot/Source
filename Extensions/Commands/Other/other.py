from discord import PartialEmoji

from Classes import Category, ShakeBot, _

############
#


class Other(Category):
    @property
    def description(self) -> str:
        return _("""Other commands without categories""")

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{GLOBE WITH MERIDIANS}")

    @property
    def label(self) -> str:
        return _("Other")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Other(bot))


#
############
