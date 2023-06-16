############
#
from enum import Enum
from importlib import reload

from discord import Interaction, Member, PartialEmoji, app_commands
from discord.ext.commands import Greedy, guild_only, hybrid_group

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc

from ..information import Information
from . import rtfm, testing

########
#


class Keys(Enum):
    discordpy = "latest"
    python = "python"
    Blue = "blue"


class rtfm_extension(Information):
    """
    rtfm_cog
    """

    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(rtfm)
        except:
            pass

    @property
    def display_emoji(self) -> str:
        return PartialEmoji(name="\N{BOOKS}")

    async def rtfm_slash_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not hasattr(self.bot, "_rtfm_cache"):
            await interaction.response.autocomplete([])
            await rtfm.build_rtfm_lookup_table()
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None
        key = interaction.command.name
        matches = rtfm.finder(current, self.bot._rtfm_cache[key])[:10]
        return [app_commands.Choice(name=m, value=m) for m in matches]

    @hybrid_group(name="rtfm")
    @guild_only()
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def rtfm(self, ctx: ShakeContext, key: Keys, entity: str) -> None:
        _(
            """View objects from certain documentation.

            RTFM is internet slang for the phrase "read the damn manual"."""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            await do.command(ctx).__await__(key.value, entity)

        except:
            if ctx.testing:
                raise Testing
            raise

    @rtfm.command(name="stats")
    @locale_doc
    async def stats(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """View the members stats of the rtfm command.
            
            Parameters
            -----------
            member: Greedy[Member]
                the members you want to get the stats from"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            await do.command(ctx=ctx).stats(member=member)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(rtfm_extension(bot))


#
############
