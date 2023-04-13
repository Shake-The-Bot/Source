############
#
from Classes import _, locale_doc, setlocale, ShakeContext, ShakeBot, is_beta
from discord import app_commands, Member, PartialEmoji
from discord.ext import commands
from importlib import reload
from typing import Optional
from . import invites
########
#
class invites_extension(commands.Cog):
    def __init__(self, bot: ShakeBot): 
        self.bot: ShakeBot = bot
        self.env = {}

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{DESKTOP COMPUTER}'))

    def category(self) -> str: 
        return "inviting"

    @commands.hybrid_command(name="invites")
    @app_commands.guild_only()
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
        if self.bot.dev:
            reload(invites)
        return await invites.command(ctx=ctx, member=member or ctx.author).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(invites_extension(bot))
#
############