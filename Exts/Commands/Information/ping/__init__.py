############
#
from discord import PartialEmoji
from importlib import reload
from . import ping, testing
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes import ShakeContext, _, locale_doc, setlocale, Testing, ShakeBot
########
#
class ping_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{CHART WITH UPWARDS TREND}')
    
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

        
        
        if ctx.testing:
            reload(testing)

        do = testing if ctx.testing else list

        try:
            await do.command(ctx=ctx).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(ping_extension(bot))
#
############