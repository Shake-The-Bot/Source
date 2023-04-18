############
#
from typing import Union, Optional
from discord import PartialEmoji, Member, User
from importlib import reload
from . import userinfo, testing
from Classes import _, locale_doc, setlocale, ShakeBot, ShakeContext, Testing
from discord.ext.commands import hybrid_command, Cog, guild_only
########
#
class userinfo_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{INFORMATION SOURCE}')
    
    def category(self) -> str: 
        return "information"

    @hybrid_command(name="userinfo", aliases=["ui"])
    @guild_only()
    @setlocale()
    @locale_doc
    async def userinfo(self, ctx: ShakeContext, user: Optional[Union[Member, User]] = None):
        _(
            """Get information about you or a specified user.
            
            Parameters
            -----------
            user: Optional[Union[Member, User]]
                @mention, ID or name."""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else userinfo

        try:    
            await do.command(ctx=ctx, user=user or ctx.author).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot): 
    await bot.add_cog(userinfo_extension(bot))
#
############