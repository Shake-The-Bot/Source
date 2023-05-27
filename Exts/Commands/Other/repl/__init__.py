############
#
from discord import PartialEmoji
from importlib import reload
from . import repl, testing
from typing import Any
from Classes import _, locale_doc, setlocale, ShakeContext, ShakeBot, Testing
from discord.app_commands import guild_only
from Classes.checks import extras
from discord.ext.commands import is_owner, Cog, command
########
#
class repl_extension(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.last: Any = None
        self.env = dict()
        try:
            reload(repl)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{WASTEBASKET}')

    def category(self) -> str: 
        return "other"

    @command(name="repl")
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
            
            Environment Variables:
                ctx     - command invocation context
                bot     - bot object
                channel - the current channel object
                author  - command author's member object
                message - the command's message object
                _       - The result of the last dev command.
            
            Parameters
            -----------
            code: str
                the code"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else repl
        try:    
            last = await do.command(ctx=ctx, code=code, env=self.env, last=self.last).__await__()
            
            if last:
                self.last = last
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(repl_extension(bot))
#
############