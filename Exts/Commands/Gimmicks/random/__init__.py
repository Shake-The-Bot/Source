############
#
from discord import PartialEmoji
from typing import Optional
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, Testing
from . import random, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
########
#
class random_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{VIDEO GAME}')

    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name="random")
    @guild_only()
    @setlocale()
    @locale_doc
    async def random(self, ctx: ShakeContext, offline: Optional[bool] = True):
        _(
            """Picks a random online user

            Parameters
            -----------
            offline: bool
                if offline is ok"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if ctx.testing else random

        try:    
            await do.command(ctx=ctx, offline=offline).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

         
########
#
async def setup(bot: ShakeBot): 
    await bot.add_cog(random_extension(bot))
#
############