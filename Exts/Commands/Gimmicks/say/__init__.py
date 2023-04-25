############
#
from typing import Optional
from discord import PartialEmoji
from importlib import reload
from . import say, testing
from discord.ext.commands import Cog, hybrid_command, guild_only
from Classes import ShakeContext, ShakeBot, _, locale_doc, setlocale, Testing
########
#
class say_extension(Cog):
    def __init__(self, bot: ShakeBot) -> None: 
        self.bot: ShakeBot = bot
        try:
            reload(say)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{SPEECH BALLOON}')
    
    def category(self) -> str: 
        return "gimmicks"
    
    @hybrid_command(name="say")
    @guild_only()
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

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.__testing = False

        do = testing if ctx.testing else say
        try:    
            await do.command(ctx=ctx, text=text, reply=reply).__await__()
    
        except:
            if ctx.testing:
                raise Testing
            raise

async def setup(bot: ShakeBot): 
    await bot.add_cog(say_extension(bot))
#
############