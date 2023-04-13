############
#
from discord import PartialEmoji
from importlib import reload
from . import invite
from Classes import ShakeBot, ShakeContext
from discord.ext.commands import guild_only, Cog, hybrid_command
from Classes.i18n import _, locale_doc, setlocale
########
#
class invite_extension(Cog):
    def __init__(self, bot) -> None:  self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{INCOMING ENVELOPE}'))

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
        if self.bot.dev:
            reload(invite)
        return await invite.command(ctx=ctx).__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(invite_extension(bot))
#
############