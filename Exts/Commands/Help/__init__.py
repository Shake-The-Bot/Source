############
#
from . import help, testing
from typing import Optional
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
from importlib import reload
from discord.ext.commands import Cog, hybrid_command, guild_only
########
#
class help_extension(Cog):
    def __init__(self, bot) -> None:
        self.bot: ShakeBot = bot
        try:
            reload(help)
        except:
            pass

    def category(self) -> str: 
        return "help_extension"

    @hybrid_command(name="help")
    @guild_only()
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
        
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False

        do = testing if ctx.testing else help

        try:
            await do.command(ctx=ctx, category=category, command=command).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise
            

        return 

async def setup(bot: ShakeBot): 
    bot.remove_command("help")
    #bot.help_command = HelpPaginatedCommand()
    await bot.add_cog(help_extension(bot))
#
############