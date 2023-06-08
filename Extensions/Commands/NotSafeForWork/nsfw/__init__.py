############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import Cog, guild_only, hybrid_group, is_nsfw, is_owner

from Classes import ShakeBot, ShakeContext, _, extras, locale_doc, setlocale


########
#
class nsfw_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot
        try:
            pass
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{WASTEBASKET}")

    @hybrid_group(name="nsfw")
    @extras(owner=True, nsfw=True)
    @guild_only()
    @is_owner
    @is_nsfw()
    @setlocale()
    @locale_doc
    async def nsfw(
        self, ctx: ShakeContext, command, amount: int
    ) -> None:  # amount: int 1-20 [-30 (pro)]
        _(
            """Find NSFW content for predefined tags.

            This command let you find a amount of posts of NSFW content that you wanted.
            NSFW: Not Safe For Work
            
            Parameters
            -----------
            command: str
                The NSFW command you want to run.

            amount: Optional[int]
                Amount of posts from 1 to 20 (or 30 with Shake+)."""
        )
        pass  # TODO: yeah..


async def setup(bot: ShakeBot):
    await bot.add_cog(nsfw_extension(bot))


#
############
