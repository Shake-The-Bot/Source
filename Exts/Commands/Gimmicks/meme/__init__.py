############
#
from importlib import reload
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras, MISSING
from . import meme
from typing import Optional
from discord.ext.commands import Cog, hybrid_command, guild_only
from discord import PartialEmoji
########
#
class meme_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{INPUT SYMBOL FOR NUMBERS}'))
    
    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name='meme')
    @extras(beta=True)
    @guild_only()
    @setlocale()
    @locale_doc
    async def meme(self, ctx: ShakeContext, subreddit: Optional[str] = None):
        _(
            """Get the latest funny memes of reddit

            Parameters
            -----------
            subreddit: Optional[str]
                an optional argument to pass a subreddit
            """
        )
        if self.bot.dev:
            reload(meme)
        return await meme.command(ctx=ctx, subreddit=subreddit or 'dankmemes').__await__()

async def setup(bot: ShakeBot): 
    await bot.add_cog(meme_extension(bot))
#
############