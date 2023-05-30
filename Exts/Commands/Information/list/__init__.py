############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..information import Information
from . import list, testing


########
#
class list_extension(Information):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(list)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{SPIRAL NOTE PAD}")

    @hybrid_command(name="list")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def list(self, ctx: ShakeContext):
        _("""list all guilds""")

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

        do = testing if ctx.testing else list

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(list_extension(bot))


#
############
