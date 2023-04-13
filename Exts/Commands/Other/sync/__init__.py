############
#
from discord import PartialEmoji, Object
from importlib import reload
from typing import Optional, Literal
from Classes import ShakeBot, ShakeContext, _, locale_doc, setlocale, extras
from . import sync
from discord.ext.commands import Greedy, guild_only, is_owner, Cog, hybrid_command
########
#
class sync_extension(Cog):
    def __init__(self, bot) -> None: 
        self.bot: ShakeBot = bot

    @property
    def display_emoji(self) -> PartialEmoji: 
        return PartialEmoji(name='\N{SATELLITE ANTENNA}')

    def category(self) -> str: 
        return "moderation"

    @hybrid_command(name="sync")
    @extras(owner=True)
    @guild_only()
    @is_owner()
    @setlocale()
    @locale_doc
    async def sync(self, ctx: ShakeContext, guilds: Greedy[Object] = None, spec: Optional[Literal["~", "*", "^"]] = None, dump: Optional[bool] = False):
        _(
            """synchronize the bot with its commands

            The synchronization is used to reload the changes.
            Synchronize when ...
            - ...commands, arguments or permissions have been added, removed or changed
            - ...a global/server command becomes a server/global command

            Parameters
            -----------
            guilds: Optional[strl]
                the guilds

            spec: Optional[Literal["~", "*", "^"]]
                the spec

            dump: Optional[bool]
                if dump"""
        )
        if self.bot.dev:
            reload(sync)
        return await sync.command(ctx=ctx, guilds=guilds, spec=spec, dump=dump).__await__()

async def setup(bot):
    await bot.add_cog(sync_extension(bot))
#
############