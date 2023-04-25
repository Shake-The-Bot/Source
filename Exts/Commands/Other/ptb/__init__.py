############
#
from discord import PartialEmoji
from importlib import reload
from typing import Optional
from . import ptb
from Classes import ShakeBot, ShakeContext, extras, _, locale_doc, setlocale, Testing
from discord.ext.commands import hybrid_command, guild_only, is_owner, Cog
########
#
class ptb_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(ptb)
        except:
            pass
    
    def category(self) -> str: 
        return "other"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{HEAVY PLUS SIGN}')
    
    @hybrid_command(name="ptb")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def ptb(self, ctx: ShakeContext, id: Optional[str] = None):
        _(
            """Temporarily adds a server/channel/user to the public test build"""
        )

        reload(ptb)
        try:
            await ptb.command(ctx, id or str(ctx.channel.id)).__await__()
        except:
            raise Testing

async def setup(bot: ShakeBot): 
    await bot.add_cog(ptb_extension(bot))
#
############