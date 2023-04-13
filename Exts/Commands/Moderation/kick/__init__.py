############
#
from discord import PartialEmoji, Member
from importlib import reload
from . import kick
from Classes import ShakeBot
from typing import Optional
from discord import app_commands
from discord.ext.commands import Greedy
from Classes.i18n import _, locale_doc, setlocale
from Classes import ShakeContext
from discord.ext import commands
########
#
class kick_extension(commands.Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji:
        return str(PartialEmoji(name="🚨"))

    def category(self) -> str:
        return "moderation"

    @commands.hybrid_command(name="kick")
    @app_commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members = True)
    @setlocale()
    @locale_doc
    async def kick(self, ctx: ShakeContext, member: Greedy[Member], *, reason: Optional[str] = None):
        _(
            """kicks a member

            Parameters
            -----------
            member: discord.Member
                the member to mute"""
        )
        if self.bot.dev:
            reload(kick)
        return await kick.command(ctx=ctx, member=member, reason=reason).__await__()

async def setup(bot):
    await bot.add_cog(kick_extension(bot))
#
############