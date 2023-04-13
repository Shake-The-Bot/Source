############
#
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import everyone
from Classes.i18n import _, locale_doc, setlocale
from discord.ext.commands import Cog, hybrid_command, guild_only, Greedy
########
#
class everyone_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{ANGRY FACE}'))
    
    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name="everyone")
    @guild_only()
    @setlocale()
    @locale_doc
    async def everyone(self, ctx: ShakeContext, member: Greedy[Member]=None):
        _(
            """Remind others how bad @everyone actually is

            With this command you can show other people with a picture/gif how unnecessary a @everyone ping is or express that someone is spamming @everyone again.

            Parameters
            -----------
            member: commands.Greedy[Member]
                the member to blame"""
        )
        if self.bot.dev:
            reload(everyone)
        return await everyone.command(ctx=ctx, member=member or [ctx.author]).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(everyone_extension(bot))
#
############