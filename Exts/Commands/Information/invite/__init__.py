############
#
from discord import PartialEmoji
from importlib import reload
from . import invite, testing
from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from discord.ext.commands import guild_only, Cog, hybrid_command
########
#
class invite_extension(Cog):
    def __init__(self, bot) -> None:  
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INCOMING ENVELOPE}')

    def category(self) -> str: 
        return "information"
    
    @hybrid_command(name="invite", aliases=["add",])
    @guild_only()
    @setlocale()
    @locale_doc
    async def invite(self, ctx: ShakeContext):
        _(
            """Invite the bot to your server.

            Of course, you can also simply add the bot via its user profile."""
        )
        
        if ctx.testing:
            reload(testing)

        do = testing if ctx.testing else invite

        try:
            await do.command(ctx=ctx).__await__()
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(invite_extension(bot))
#
############