############
#
from typing import Optional
from importlib import reload
from . import serverinfo
from Classes import ShakeBot, ShakeContext, GuildNotFound, _, locale_doc, setlocale
from discord.ext.commands import Cog, hybrid_command, GuildNotFound as _GuildNotFound, guild_only
from discord.ext.commands.converter import GuildConverter
from discord import PartialEmoji
########
#
class server_extension(Cog):
    """
    server_cog
    """
    def __init__(self, bot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{INFORMATION SOURCE}'))

    def category(self) -> str: 
        return "information"

    @hybrid_command(name=('serverinfo'), aliases=["si"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def server(self, ctx: ShakeContext, guild: Optional[str] = None):
        _(
            """Get information about a specific server.
            
            This command will show you some information about a server.

            Parameters
            -----------
            guild: Optional[str]
                the guild name or id to get information about"""
        )
        if self.bot.dev:
            reload(serverinfo)
        try:
            guild = await GuildConverter().convert(self, str(guild or ctx.guild.id))
        except _GuildNotFound as argument:
            raise GuildNotFound(argument, "Either this server does not exist or I am not on it.")
        return await serverinfo.serverinfo_command(ctx=ctx, guild=guild).__await__()

async def setup(bot): 
    await bot.add_cog(server_extension(bot))
#
############