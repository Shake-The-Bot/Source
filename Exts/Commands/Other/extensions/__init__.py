############
#
from discord import PartialEmoji
from importlib import reload
from . import extensions, testing
from Classes.useful import Methods
from Classes import ShakeContext, ShakeBot, ValidCog, extras, _, locale_doc, setlocale, Testing
from discord.ext.commands import guild_only, is_owner, Greedy, Cog, hybrid_command
########
#
class extensions_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(extensions)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
    
    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name="extensions")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def extensions(self, ctx: ShakeContext, command: Methods, *, extension: Greedy[ValidCog]):
        _(
            """Reloads, unloads or loads extensions of the bot
            
            Parameters
            -----------
            command: Methods[load, unload, reload]
                re- un- or loading the <extensions>

            extension: Greedy[ValidCog]
                the extension(s) you want to re- un- or load"""
        )
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else extensions

        try:
            await do.command(ctx=ctx, method=command, extension=extension).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(extensions_extension(bot))
#
############