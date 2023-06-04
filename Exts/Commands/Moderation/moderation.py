from discord import PartialEmoji

from Classes import Category, ShakeBot, _

############
#


class Moderation(Category):
    @property
    def description(self) -> str:
        return _(
            """Moderation related commands.
            (Each of these commands requires certain authorization)."""
        )

    @property
    def emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{POLICE OFFICER}")

    @property
    def label(self) -> str:
        return _("Moderation")

    @property
    def title(self) -> str:
        return f"{self.emoji} » {self.label}"

    @property
    def describe(self) -> bool:
        return False


async def setup(bot: ShakeBot):
    await bot.add_cog(Moderation(bot))


#
############
