############
#
from discord import PartialEmoji, Member
from importlib import reload
from . import mute
from Classes import ShakeBot
from discord.ext.commands import Greedy, hybrid_command, has_permissions, Cog, guild_only
from Classes.i18n import _, locale_doc, setlocale
from Classes import ShakeContext
########
#
class mute_extension(Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji:
        return str(PartialEmoji(name="🚨"))

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
        if self.bot.dev:
            reload(mute)
        return await mute.mute_command(ctx=ctx, member=member, time=time).__await__()

async def setup(bot):
    await bot.add_cog(mute_extension(bot))
#
############