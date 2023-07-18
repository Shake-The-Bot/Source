############
#
from typing import Literal, Optional

from discord import HTTPException, Object
from discord.ext.commands import Greedy

from Classes import ShakeCommand, _


########
#
class command(ShakeCommand):
    def __init__(
        self,
        ctx,
        guilds: Greedy[Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
        dump: Optional[bool] = False,
    ) -> None:
        super().__init__(ctx)
        self.guilds: Greedy[Object] = guilds
        self.spec: Optional[Literal["~", "*", "^"]] = spec
        self.dump = dump

    async def __await__(self):
        await self.ctx.defer(ephemeral=True)
        if not self.guilds:
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
                try:
                    synced = await self.ctx.bot.tree.sync(guild=guild)
                except HTTPException:
                    pass

        if self.dump:
            await self.ctx.chat(
                content=f"<{await self.bot.dump(str(synced))}>", ephemeral=True
            )

        content = (
            _("{amount} Command*s to the current guild synchronized.")
            if self.spec
            else _("{amount} Command*s globally synchronized.")
        )
        await self.ctx.chat(
            content=content.format(
                amount=len(synced),
            ),
            ephemeral=True,
        )
        return


#
############
