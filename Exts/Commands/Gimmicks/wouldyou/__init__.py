############
#
from importlib import reload
from typing import Literal, Optional

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import testing, wouldyou


########
#
class wouldyou_extension(Gimmicks):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(wouldyou)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="scale", id=1099618823348437032)

    @hybrid_command(name="wouldyou")
    @extras(beta=True)
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def wouldyou(
        self,
        ctx: ShakeContext,
        utility: Literal["useful", "useless"] = "useless",
        voting: Optional[bool] = True,
        rather: Optional[bool] = False,
    ) -> None:
        _(
            """Random selection of two counterparts 
            
            The command presents the user with a random selection of two concepts, items, or the like, both of which are labeled as either useful or useless. 
            Users in the chat can then choose which of the two counterparts they think is better or more useful before the overall trend of opinions is displayed after the timeout expires. 
            This command can serve as a fun way to expand users' judgment and preferences.

            Parameters
            -----------
            utility: Literal['useful', 'useless']
                useful or useless counterparts?

            voting: Optional[bool]
                should we save answers and compare at the end?

            rather: Optional[bool]
                ehm
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

        do = testing if ctx.testing else wouldyou
        try:
            await do.command(
                ctx=ctx, utility=utility, voting=voting, rather=rather
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(wouldyou_extension(bot))


#
############
