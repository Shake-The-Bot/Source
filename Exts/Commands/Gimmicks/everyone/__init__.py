############
#
from importlib import reload

from discord import Member, PartialEmoji
from discord.ext.commands import Greedy, guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import everyone, testing


########
#
class everyone_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(everyone)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{ANGRY FACE}")

    @hybrid_command(name="everyone")
    @guild_only()
    @setlocale()
    @locale_doc
    async def everyone(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """Remind others how bad @everyone actually is

            With this command you can show other people with a picture/gif how unnecessary a @everyone ping is or express that someone is spamming @everyone again.

            Parameters
            -----------
            member: commands.Greedy[Member]
                the member to blame"""
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
        do = testing if ctx.testing else everyone

        try:
            await do.command(ctx=ctx, member=member or [ctx.author]).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(everyone_extension(bot))


#
############
