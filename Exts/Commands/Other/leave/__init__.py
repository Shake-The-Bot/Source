############
#
from discord import PartialEmoji
from importlib import reload
from Classes import ShakeContext, ShakeBot, _, locale_doc, setlocale, extras
from typing import Optional
from . import leave
from discord.ext.commands import hybrid_command, guild_only, is_owner, Cog
########
#
class leave_extension(Cog):
    def __init__(self, bot) -> None: self.bot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='blobleave', animated=True, id=1058033660755972219))
    
    def category(self) -> str: 
        return "other"
    
    @hybrid_command(name='leave')
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def leave(self, ctx: ShakeContext, *, guild: Optional[int] = None):
        _(
            """Leave a guild

            Parameters
            -----------
            guild: int
                the ID of the server"""
        )
        if self.bot.dev:
            reload(leave)
        return await leave.command(ctx=ctx, guild=guild).__await__()
            

async def setup(bot: ShakeBot): 
    await bot.add_cog(leave_extension(bot))
#
############