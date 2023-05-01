############
#
from Classes import _, locale_doc, setlocale, ShakeContext, ShakeBot, is_beta, Testing
from discord import app_commands, Member, PartialEmoji
from discord.ext.commands import Cog, hybrid_command, guild_only
from importlib import reload
from typing import Optional
from . import invites, testing
########
#
class invites_extension(Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        try:
            reload(invites)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{DESKTOP COMPUTER}')

    def category(self) -> str: 
        return "inviting"

    @hybrid_command(name="invites")
    @guild_only()
    @is_beta()
    @setlocale()
    @locale_doc
    async def invites(self, ctx: ShakeContext, *, member: Optional[Member] = None) -> None:
        _(
            """See the users amount of invites.

            Parameters
            -----------
            member: discord.Member
                the member
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else invites

        try:    
            await do.command(ctx=ctx, member=member or ctx.author).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise
        

async def setup(bot: ShakeBot): 
    await bot.add_cog(invites_extension(bot))
#
############