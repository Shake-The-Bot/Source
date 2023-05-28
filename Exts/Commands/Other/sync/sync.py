############
#
from discord.ext.commands import Greedy
from discord import Object, HTTPException
from typing import Optional, Literal
from Classes import ShakeBot, ShakeContext
from discord.ext import commands
from Classes import _
########
#
class command():
    def __init__(self, ctx, guilds: Greedy[Object], spec: Optional[Literal["~", "*", "^"]] = None, dump: Optional[bool] = False) -> None:
        self.bot: ShakeBot = ctx.bot
        self.guilds: Greedy[Object] = guilds
        self.spec: Optional[Literal["~", "*", "^"]] = spec
        self.dump = dump
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        await self.ctx.defer(ephemeral=True)
        if not self.guilds:
            if not (guild := self.ctx.guild):
                raise commands.NoPrivateMessage()

            if self.spec == "~":
                synced = await self.ctx.bot.tree.sync(guild=guild)
            elif self.spec == "*":
                self.ctx.bot.tree.copy_global_to(guild=guild)
                synced = await self.ctx.bot.tree.sync(guild=guild)
            elif self.spec == "^":
                self.ctx.bot.tree.clear_commands(guild=self.ctx.guild)
                await self.bot.tree.sync(guild=self.ctx.guild)
                synced = []
            else:
                synced = await self.ctx.bot.tree.sync()
        else:
            for guild in self.guilds:
                try: synced = await self.ctx.bot.tree.sync(guild=guild)
                except HTTPException: pass
        
        if self.dump:
            await self.ctx.smart_reply(content=f'<{await self.bot.dump(str(synced))}>', ephemeral=True)
        await self.ctx.smart_reply(
            content=("{amount} Command*s {where} synchronized.").format(
                amount=len(synced), where=_("globally") if self.spec is None else _("to the current guild")
            ), ephemeral=True
        )
        return
#
############