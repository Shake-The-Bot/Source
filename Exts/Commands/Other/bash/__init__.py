############
#
from discord import PartialEmoji
from importlib import reload
from . import bash, testing
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext, extras, Testing
from discord.ext.commands import Cog, command, guild_only, is_owner
########
#
class bash_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot
        try:
            reload(bash)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{DESKTOP COMPUTER}')

    def category(self) -> str: 
        return "other"

    @command(name="bash")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def bash(self, ctx: ShakeContext, *, command: str) -> None:
        _(
            """Run shell commands.

            Parameters
            -----------
            command: str
                the command"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else bash

        try:    
            await do.command(ctx=ctx, command=command).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(bash_extension(bot))
#
############