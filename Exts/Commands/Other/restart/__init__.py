############
#
from discord import PartialEmoji
from importlib import reload
from . import restart, testing
from Classes import ShakeContext, ShakeBot, extras, _, locale_doc, setlocale, Testing
from discord.ext.commands import guild_only, is_owner, Cog, command
########
#
class restart_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(restart)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}')
    
    def category(self) -> str: 
        return "other"
    
    @command(name="restart")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def restart(self, ctx: ShakeContext):
        _(
            """Stops and starts the bot like in a regular Restart"""
        )
        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False

        do = testing if ctx.testing else restart

        try:
            await do.command(ctx=ctx).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(restart_extension(bot))
#
############