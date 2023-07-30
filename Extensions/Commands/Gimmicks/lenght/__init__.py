############
#
from importlib import reload

from discord import Member, PartialEmoji
from discord.ext.commands import Greedy, guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..gimmicks import Gimmicks
from . import lenght, testing


########
#
class lenght_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(lenght)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{VIDEO GAME}")

    @hybrid_command(name="lenght")
    @guild_only()
    @setlocale()
    @locale_doc
    async def lenght(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """Get a random length depending on the user

            With this command you can find out, using a very clever and definitely not random generator,
            which lenght would with to an user.
            
            __Please note__: If you don't specify a user, I might reveal your lenght as well.

            Parameters
            -----------
            member: Greedy[Member]
                the member to reveal the lenght of"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

        do = testing if ctx.testing else lenght
        try:
            await do.command(ctx=ctx, member=member or [ctx.author]).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


########
#
async def setup(bot: ShakeBot):
    await bot.add_cog(lenght_extension(bot))


#
############
