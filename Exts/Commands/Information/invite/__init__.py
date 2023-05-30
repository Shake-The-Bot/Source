############
#
from importlib import reload

from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale

from ..information import Information
from . import invite, testing


########
#
class invite_extension(Information):
    def __init__(self, bot) -> None:
        super().__init__(bot=bot)
        try:
            reload(invite)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{INCOMING ENVELOPE}")

    @hybrid_command(
        name="invite",
        aliases=[
            "add",
        ],
    )
    @guild_only()
    @setlocale()
    @locale_doc
    async def invite(self, ctx: ShakeContext):
        _(
            """Invite the bot to your server.

            Of course, you can also simply add the bot via its user profile."""
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

        do = testing if ctx.testing else invite

        try:
            await do.command(ctx=ctx).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(invite_extension(bot))


#
############
