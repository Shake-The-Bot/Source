############
#
from typing import Any, Dict, Optional

from discord.ext.commands.errors import ExtensionError

from Classes import ExtensionMethods, Format, ShakeCommand, ShakeEmbed, extshandler
from Classes.converter import ValidExt


########
#
class command(ShakeCommand):
    def __init__(self, ctx, method: ExtensionMethods, extension: ValidExt):
        super().__init__(ctx)
        self.method: ExtensionMethods = method
        self.extension: str = extension

    async def __await__(self):
        handling: Dict[str, Any] = await extshandler(
            ctx=self.ctx, method=self.method, extensions=self.extension
        )

        embed = ShakeEmbed.default(ctx=self.ctx)

        failures: int = 0
        successes = list()
        for i, (extension, handle) in enumerate(handling.items(), 1):
            error: Optional[ExtensionError] = (
                getattr(handle, "original", handle) if handle else None
            )
            ext = ".../ " + extension.replace(".", "/") + ".py"
            name = Format.multicodeblock(ext)
            if error:
                failures += 1
                value = "{}".format(str(error).replace(extension, ext))
                embed.add_field(name="❌ " + ext, value=value)
            else:
                successes.append(name)

        if bool(successes):
            embed.insert_field_at(
                index=0,
                name=f"{self.method.name.lower().capitalize()}ed",
                value="\n".join(successes),
            )
        return await self.ctx.chat(embed=embed)


#
############
