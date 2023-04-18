############
#
from discord import PartialEmoji, Member
from importlib import reload
from . import kick, testing
from Classes import ShakeBot, _, locale_doc, setlocale, Testing, ShakeContext
from typing import Optional
from discord.ext.commands import Greedy, Cog, hybrid_command, has_permissions, bot_has_permissions, guild_only
########
#
class kick_extension(Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="🚨")

    def category(self) -> str:
        return "moderation"

    @hybrid_command(name="kick")
    @guild_only()
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members = True)
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

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else kick

        try:    
            await do.command(ctx=ctx, member=member, reason=reason).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot):
    await bot.add_cog(kick_extension(bot))
#
############