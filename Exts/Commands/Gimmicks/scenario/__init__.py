############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import scenario, testing


########
#
class scenario_extension(Gimmicks):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(scenario)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(animated=True, name="shakeloading", id=1092832911163654245)

    @hybrid_command(name="scenario")
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def scenario(self, ctx: ShakeContext) -> None:
        _(
            """What would you do in this scenario? Find out!

            With this command, you are presented with a hypothetical situation and asked to say what you would do. 
            Each time, you will be presented with a situation, so you will be challenged over and over again.
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

        do = testing if ctx.testing else scenario

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(scenario_extension(bot))


#
############
