############
#
from discord import PartialEmoji
from importlib import reload
from . import wouldyou
from typing import Optional, Literal
from Classes.i18n import _, locale_doc, setlocale
from discord.ext.commands import Cog, hybrid_command, guild_only
from Classes import ShakeBot, ShakeContext, extras
########
#
class wouldyou_extension(Cog):
    def __init__(self, bot): 
        self.bot: ShakeBot = bot

    def category(self) -> str: 
        return "gimmicks"

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{SCALES}'))

    @hybrid_command(name="wouldyou")
    @extras(beta=True)
    @guild_only()
    @setlocale(guild=True)
    @locale_doc
    async def wouldyou(self, ctx: ShakeContext, utility: Literal['useful', 'useless'] = 'useful', voting: Optional[bool] = True, rather: Optional[bool] = False) -> None:
        _(
            """Random selection of two counterparts 
            
            The command presents the user with a random selection of two concepts, items, or the like, both of which are labeled as either useful or useless. 
            Users in the chat can then choose which of the two counterparts they think is better or more useful before the overall trend of opinions is displayed after the timeout expires. 
            This command can serve as a fun way to expand users' judgment and preferences.

            Parameters
            -----------
            utility: Literal['useful', 'useless']
                useful or useless counterparts?

            voting: Optional[bool]
                should we save answers and compare at the end?

            rather: Optional[bool]
                ehm
            """
        )
        if self.bot.dev:
            reload(wouldyou)
        await wouldyou.command(ctx=ctx, utility=utility, voting=voting, rather=rather).__await__(True)
    
async def setup(bot): 
    await bot.add_cog(wouldyou_extension(bot))
#
############