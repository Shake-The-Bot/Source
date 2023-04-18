############
#
from discord import PartialEmoji
from importlib import reload
from . import repl, testing
from Classes import _, locale_doc, setlocale, ShakeContext, ShakeBot, Testing
from discord.app_commands import guild_only
from Classes.checks import extras
from discord.ext.commands import is_owner,  Cog, hybrid_command
########
#
class repl_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        self.env = {}

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{WASTEBASKET}')

    def category(self) -> str: 
        return "other"

    @hybrid_command(name="repl")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def repl(self, ctx: ShakeContext, *, code: str) -> None:
        _(
            """Run your own xyz codes.
            
            You can simply specify this code as an argument and also in quotes (`).
            Optionally you can use common attributes like ctx, bot etc. in the code.
            
            Parameters
            -----------
            code: str
                the code"""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else repl

        try:    
            await do.command(ctx=ctx, code=code, env=self.env).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(repl_extension(bot))
#
############