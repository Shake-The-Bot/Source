############
#
from importlib import reload
from typing import Optional

from discord import PartialEmoji
from discord.ext.commands import command, guild_only, is_owner

from Classes import ShakeBot, ShakeContext, Testing, _, extras, locale_doc, setlocale

from ..other import Other
from . import ptb


########
#
class ptb_extension(Other):
    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(ptb)
        except:
            pass

    def category(self) -> str:
        return "other"

    @property
    def display_emoji(self) -> PartialEmoji:
        return PartialEmoji(name="\N{HEAVY PLUS SIGN}")

    @command(name="ptb")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def ptb(self, ctx: ShakeContext, id: Optional[str] = None):
        _("""Temporarily adds a server/channel/user to the public test build""")

        reload(ptb)
        try:
            await ptb.command(ctx, id or str(ctx.channel.id)).__await__()
        except:
            raise Testing


async def setup(bot: ShakeBot):
    await bot.add_cog(ptb_extension(bot))


#
############
