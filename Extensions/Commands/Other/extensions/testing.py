############
#
from typing import Any, Dict, Optional

from discord.ext.commands.errors import ExtensionError

from Classes import ExtensionMethods, ShakeCommand, ShakeEmbed, TextFormat, cogshandler
from Classes.converter import ValidCog


########
#
class command(ShakeCommand):
    def __init__(self, ctx, method: ExtensionMethods, extension: ValidCog):
        super().__init__(ctx)
        self.method: ExtensionMethods = method
        self.extension: str = extension

    async def __await__(self):
        handling: Dict[str, Any] = await cogshandler(
            ctx=self.ctx, method=self.method, extensions=self.extension
        )

        embed = ShakeEmbed()

        failures: int = 0
        successes = list()
        for i, (extension, handle) in enumerate(handling.items(), 1):
            error: Optional[ExtensionError] = (
                getattr(handle, "original", handle) if handle else None
            )

            ext = f"`{extension}`"
            name = f"` {i}. ` {ext}"
            if error:
                failures += 1
                value = "{}".format(str(error).replace(extension, ext))
                embed.add_field(name="❌ " + name, value=value)
            else:
                successes.append(name)

        if bool(successes):
            embed.insert_field_at(
                index=0,
                name=f"{self.method.name.lower().capitalize()}ed",
                value="\n".join(successes),
            )
        emoji = "☑️" if failures < len(handling) / 2 else "❌"
        embed.description = TextFormat.bold(
            f"{emoji} {len(handling.keys()) - failures} / {len(handling.keys())} extensions successfully {self.method.name.lower()}ed."
        )
        return await self.ctx.chat(embed=embed)


#
############
