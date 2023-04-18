############
#
from discord import PartialEmoji, Member
from importlib import reload
from . import mute, testing
from discord.ext.commands import Greedy, hybrid_command, has_permissions, Cog, guild_only
from Classes.i18n import _, locale_doc, setlocale
from Classes import ShakeContext, ShakeBot, Testing
########
#
class mute_extension(Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="🚨")

    def category(self) -> str:
        return "moderation"

    @hybrid_command(name="mute", aliases=["timeout"])
    @guild_only()
    @has_permissions(administrator=True)
    @setlocale()
    @locale_doc
    async def mute(
        self, ctx: ShakeContext, 
        member: Greedy[Member], time: str = "1h"
    ):
        _(
            """put a user in the timeout

            Parameters
            -----------
            member: discord.Member
                the member to mute

            time: discord.Member
                the time"""
        )

        if ctx.testing:
            reload(testing)
        do = testing if ctx.testing else mute

        try:    
            await do.command(ctx=ctx, member=member, time=time).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot):
    await bot.add_cog(mute_extension(bot))
#
############