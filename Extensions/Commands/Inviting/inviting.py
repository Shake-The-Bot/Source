############
#
from discord import PartialEmoji

from Classes import Category, ShakeBot, _


########
#
class inviting(Category):
    @property
    def description(self) -> str:
        return _(
            """Useful Commands to track invites and and get some members with these"""
        )

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INCOMING ENVELOPE}")

    def long_doc_title(self) -> str:
        return f"{self.display_emoji}︱{self.label}"

    @property
    def label(self) -> str:
        return _("Inviting")

    @property
    def describe(self) -> bool:
        return False

    @property
    def help_command_title(self) -> str:
        return "invite Befehle"


async def setup(bot: ShakeBot):
    await bot.add_cog(inviting(bot))


#
############
