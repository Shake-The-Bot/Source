############
#
from discord import PartialEmoji
from importlib import reload
from . import ping
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes.i18n import _, locale_doc, setlocale
from discord import app_commands
from Classes import ShakeContext
########
#
class ping_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{CHART WITH UPWARDS TREND}'))
    
    def category(self) -> str: 
        return "information"

    @hybrid_command(name="ping")
    @guild_only()
    @setlocale()
    @locale_doc
    async def ping(self, ctx: ShakeContext):
        _(
            """Get some ping"""
        )
        if self.bot.dev:
            reload(ping)
        return await ping.ping_command(ctx=ctx).__await__()

async def setup(bot): 
    await bot.add_cog(ping_extension(bot))
#
############