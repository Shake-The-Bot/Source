############
#
from typing import Optional
from discord import PartialEmoji
from importlib import reload
from . import say
from Classes.i18n import _, locale_doc, setlocale
from discord.ext import commands
from discord import app_commands
from Classes import ShakeContext, ShakeBot
########
#
class say_extension(commands.Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return str(PartialEmoji(name='\N{SPEECH BALLOON}'))
    
    def category(self) -> str: 
        return "gimmicks"
    
    @commands.hybrid_command(name="say")
    @setlocale()
    @locale_doc
    async def say(self, ctx: ShakeContext, reply: Optional[bool] = True, *, text: str):
        _(
            """I will say whatever you tell me to say.

            Parameters
            -----------
            reply: Optional[bool]
                True or False whether the bot should reply to you

            text: str
                What the bot should echo"""
        )
        if self.bot.dev:
            reload(say)
        return await say.command(ctx=ctx, text=text, reply=reply).__await__()

async def setup(bot): 
    await bot.add_cog(say_extension(bot))
#
############