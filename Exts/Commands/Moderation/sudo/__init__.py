############
#
from importlib import reload
from typing import Optional, Union

from discord import Member, PartialEmoji, TextChannel, User
from discord.ext.commands import guild_only, has_permissions, hybrid_command

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..moderation import Moderation
from . import sudo, testing


########
#
class sudo_extension(Moderation):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(sudo)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{WASTEBASKET}")

    @hybrid_command(name="sudo")
    @extras(permissions=True)
    @has_permissions(administrator=True)
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def sudo(
        self,
        ctx: ShakeContext,
        channel: Optional[TextChannel],
        user: Union[Member, User],
        command: str,
        *,
        arguments: Optional[str] = None
    ):
        _(
            """execute commands with the rights of another user

            You can specify who executes this command in which text channel"

            Parameters
            -----------
            channel: Optional[TextChannel]
                the channel

            user: Union[Member, User]
                the user

            command: str
                the command

            arguments: Optional[str]
                the arguments
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else sudo

        try:
            await do.command(
                ctx=ctx, channel=channel, user=user, command=command, args=arguments
            ).__await__()

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(sudo_extension(bot))


#
############
