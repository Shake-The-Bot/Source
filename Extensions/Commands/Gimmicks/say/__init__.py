############
#
from importlib import reload
from typing import Optional

from Classes import ShakeBot, ShakeContext, Testing, _, locale_doc, setlocale
from discord import PartialEmoji
from discord.ext.commands import guild_only, hybrid_command

from ..gimmicks import Gimmicks
from . import say, testing


########
#
class say_extension(Gimmicks):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(say)
        except:
            pass

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{SPEECH BALLOON}")

    @hybrid_command(name="say")
    @guild_only()
    @locale_doc
    @setlocale()
    async def say(self, ctx: ShakeContext, reply: Optional[bool] = False, *, text: str):
        _(
            """I will say whatever you tell me to say, except...
            Speak as if you were me. URLs/Invites not allowed!

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
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False

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
