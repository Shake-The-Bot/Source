from discord import PartialEmoji

from Classes import Category, ShakeBot, _

############
#


class Gimmicks(Category):
    @property
    def description(self) -> str:
        return _("""Commands for fun and distraction""")

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{GAME DIE}")

    @property
    def label(self) -> str:
        return _("Gimmicks")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Gimmicks(bot))


#
############
