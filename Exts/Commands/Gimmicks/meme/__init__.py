############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import meme, testing


########
#
class meme_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(meme)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INPUT SYMBOL FOR NUMBERS}")

    def category(self) -> str:
        return "gimmicks"

    @hybrid_command(name="meme")
    @extras(beta=True)
    @guild_only()
    @setlocale()
    @locale_doc
    async def meme(self, ctx: ShakeContext, subreddit: Optional[str] = None):
        _(
            """Get the latest funny memes of reddit

            Parameters
            -----------
            subreddit: Optional[str]
                an optional argument to pass a subreddit
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                ctx.testing = False

        do = testing if ctx.testing else meme
        try:
            await do.command(ctx=ctx, subreddit=subreddit or "dankmemes").__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(meme_extension(bot))


#
############
