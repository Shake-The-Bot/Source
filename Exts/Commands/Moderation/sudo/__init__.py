############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional, Union
from discord import TextChannel, Member, User
from . import do
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras
from discord.ext.commands import Cog, hybrid_command, is_owner, guild_only
########
#
class sudo_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{WASTEBASKET}')

    def category(self) -> str: 
        return "moderation"


    @hybrid_command(name="sudo")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def sudo(self, ctx: ShakeContext, channel: Optional[TextChannel], user: Union[Member, User], command: str, *, arguments: Optional[str] = None):
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
        if self.bot.dev:
            reload(do)
        return await do.sudo_command(ctx=ctx, channel=channel, user=user, command=command, args=arguments).__await__()

async def setup(bot: ShakeBot):
    await bot.add_cog(sudo_extension(bot))
#
############