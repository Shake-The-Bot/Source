############
#
from . import help
from typing import Optional
from Classes import ShakeBot, ShakeContext
from importlib import reload
from discord.ext import commands
from discord import app_commands
from Classes.i18n import _, locale_doc, setlocale
########
#
class help_extension(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "help_extension"

    @commands.hybrid_command(name="help")
    @app_commands.guild_only()
    @setlocale()
    @locale_doc
    async def help(self, ctx: ShakeContext, category: Optional[str]=None, command: Optional[str]=None):
        _(
            """Shows all Shake bot commands and provides helpful links
        
            Parameters
            -----------
            category: Optional[str]
                the category

            command: Optional[str]
                the command   
            """
        )
        if self.bot.dev:
            reload(help)
        await help.command(ctx=ctx, category=category, command=command).__await__()
        return 

async def setup(bot: ShakeBot): 
    bot.remove_command("help")
    #bot.help_command = HelpPaginatedCommand()
    await bot.add_cog(help_extension(bot))
#
############