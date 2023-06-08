############
#
from typing import Any, Dict, Optional

from discord.ext.commands.errors import ExtensionError

from Classes import ExtensionMethods, ShakeBot, ShakeContext, ShakeEmbed, cogshandler
from Classes.converter import ValidCog


########
#
class command:
    def __init__(
        self, ctx: ShakeContext, method: ExtensionMethods, extension: ValidCog
    ):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.method: ExtensionMethods = method
        self.extension: str = extension

    async def __await__(self):
        handling: Dict[str, Any] = await cogshandler(
            ctx=self.ctx, method=self.method, extensions=self.extension
        )

        embed = ShakeEmbed()

        failures: int = 0
        for i, (extension, handle) in enumerate(handling, 1):
            error: Optional[ExtensionError] = (
                getattr(handle, "original", handle) if handle else None
            )

            ext = f"`{extension}`"
            name = f"` {i}. ` {ext}"
            if error:
                failures += 1
                value = "> ❌ {}".format(str(error).replace(extension, ext))
            else:
                value = f"> ☑️ {self.method.name.lower().capitalize()}ed"
            embed.add_field(name=name, value=value)

        embed.description = f"**{len(handling.keys()) - failures} / {len(handling.keys())} extensions successfully {self.method.name.lower()}ed.**"
        return await self.ctx.chat(embed=embed)


#
############
