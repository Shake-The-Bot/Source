############
#
from discord import PartialEmoji
from importlib import reload
from . import channelinfo, testing
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext, Testing
########
#
class channelinfo_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        try:
            reload(channelinfo)
        except:
            pass
    
    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INPUT SYMBOL FOR LATIN SMALL LETTERS}')

    def category(self) -> str: 
        return "information"

    @hybrid_command(name="channelinfo", aliases=["ci"],)
    @guild_only()
    @setlocale()
    @locale_doc
    async def channelinfo(self, ctx: ShakeContext, *, characters: str) -> None:
        _(
            """Get information about a specific channel.
            
            This command will show you some information about a channel.

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
                ctx.testing = False

        do = testing if ctx.testing else channelinfo

        try:
            await do.command(ctx=ctx, characters=characters).__await__()
        
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(channelinfo_extension(bot))
#
############