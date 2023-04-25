############
#
from typing import Optional
from importlib import reload
from . import serverinfo, testing
from Classes import ShakeBot, ShakeContext, GuildNotFound, _, locale_doc, setlocale, Testing
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
        return PartialEmoji(name='\N{INFORMATION SOURCE}')

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

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False
        do = testing if ctx.testing else serverinfo

        try:    
            try:
                guild = await GuildConverter().convert(self, str(guild or ctx.guild.id))
            except _GuildNotFound as argument:
                raise GuildNotFound(argument, _("Either this server does not exist or I am not on it."))
            await do.command(ctx=ctx, guild=guild).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(server_extension(bot))
#
############