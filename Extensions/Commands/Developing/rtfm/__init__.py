############
#
from enum import Enum
from importlib import reload
from io import BytesIO
from os import path
from re import compile
from typing import Generator, Optional
from zlib import decompressobj

from discord import Interaction, Member, PartialEmoji, app_commands
from discord.app_commands import Choice, choices
from discord.ext.commands import Greedy, guild_only, hybrid_group, is_owner

from Classes import (
    ShakeBot,
    ShakeContext,
    Testing,
    Types,
    _,
    examples,
    locale_doc,
    setlocale,
)

from ..developing import Developing
from . import rtfm, testing

########
#


class SphinxObjectFileReader:
    BUFSIZE = 16 * 1024

    def __init__(self, buffer: bytes):
        self.stream = BytesIO(buffer)

    def readline(self) -> str:
        return self.stream.readline().decode("utf-8")

    def skipline(self) -> None:
        self.stream.readline()

    def read_compressed_chunks(self) -> Generator[bytes, None, None]:
        decompressor = decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self) -> Generator[str, None, None]:
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


def parse_object_inv(stream: SphinxObjectFileReader, url: str) -> dict[str, str]:
    result: dict[str, str] = {}

    inv_version = stream.readline().rstrip()

    if inv_version != "# Sphinx inventory version 2":
        raise RuntimeError("Invalid objects.inv file version.")

    projname = stream.readline().rstrip()[11:]
    version = stream.readline().rstrip()[11:]

    line = stream.readline()
    if "zlib" not in line:
        raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

    entry_regex = compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
    for line in stream.read_compressed_lines():
        match = entry_regex.match(line.rstrip())
        if not match:
            continue

        name, directive, prio, location, dispname = match.groups()
        domain, _, subdirective = directive.partition(":")
        if directive == "py:module" and name in result:
            continue

        if directive == "std:doc":
            subdirective = "label"

        if location.endswith("$"):
            location = location[:-1] + name

        key = name if dispname == "-" else dispname
        prefix = f"{subdirective}:" if domain == "std" else ""

        if projname == "discord.py":
            key = key.replace("discord.ext.commands.", "").replace("discord.", "")

        result[f"{prefix}{key}"] = path.join(url, location)

    return result


class Keys(Enum):
    latest = "latest"
    stable = "stable"
    python = "python"
    peps = "peps"


class rtfm_extension(Developing):
    """
    rtfm_cog
    """

    def __init__(self, bot: ShakeBot) -> None:
        super().__init__(bot=bot)
        try:
            reload(rtfm)
        except:
            pass
        bot.cache.setdefault("rtfm", dict())

    @property
    def display_emoji(self) -> str:
        return PartialEmoji(name="\N{BOOKS}")

    async def build_rtfm_lookup_table(self):
        cache: dict[str, dict[str, str]] = {}
        for key, d in Types.Manuals.value.items():
            cache[key] = {}
            async with self.bot.session.get(d["url"] + "/objects.inv") as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        "Cannot build rtfm lookup table, try again later."
                    )

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = parse_object_inv(stream, d["url"])

        self.bot.cache["rtfm"] = cache

    async def cog_load(self):
        # if not bool(self.bot.cache["rtfm"]):
        await self.build_rtfm_lookup_table()

    async def rtfm_slash_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not bool(self.bot.cache["rtfm"]):
            await interaction.response.autocomplete([])
            await rtfm.build_rtfm_lookup_table(self.bot)
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None
        key = interaction.command.name
        matches = rtfm.finder(current, self.bot.cache["rtfm"][key])[:10]
        return [app_commands.Choice(name=m, value=m) for m in matches]

    @hybrid_group(name="rtfm", invoke_without_command=True)
    @guild_only()
    @setlocale()
    @is_owner()
    @locale_doc
    async def rtfm(
        self,
        ctx: ShakeContext,
        key: Optional[str] = None,
        *,
        entity: Optional[str] = None,
    ) -> None:
        _(
            """RTFM is internet slang for the phrase "read the damn manual".
            This also applies to this command, with the help of which you can get the URLs to the documentation for various things"""
        )
        await self.search(ctx, key=key, entity=entity)

    @rtfm.command(name="search")
    @guild_only()
    @is_owner()
    @choices(
        key=[
            Choice(name="discord.py latest", value="latest"),
            Choice(name="discord.py stable", value="stable"),
            Choice(name="python", value="python"),
        ]
    )
    @setlocale()
    @locale_doc
    @examples(key=Keys)
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    async def search(
        self,
        ctx: ShakeContext,
        key: Optional[str] = None,
        *,
        entity: Optional[str] = None,
    ) -> None:
        _(
            """View objects from certain documentation.

            Parameters
            -----------
            key: Optional[str]
                the documentation key (python, discord, ...). 
                Defaults to ``python``

            entity: Optional[str]
                the thing you want to get information about (getattr, ctx.command, ...). 
                Defaults to ``None`` and returning the ``key`` website url
            """
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            default = "python"
            if key is None:
                key = default
            else:
                try:
                    lowered = key.lower()
                    key = Keys[lowered].value
                except KeyError:
                    if entity is None:
                        entity = key
                        key = default
                    else:
                        return await ctx.send(
                            "Wrong key... know what you do!", ephemeral=True
                        )
            await do.command(ctx).__await__(key, entity)

        except:
            if ctx.testing:
                raise Testing
            raise

    @rtfm.command(name="stats")
    @setlocale()
    @is_owner()
    @locale_doc
    async def stats(self, ctx: ShakeContext, member: Greedy[Member] = None):
        _(
            """View the members stats of the rtfm command.
            
            Parameters
            -----------
            member: Greedy[Member]
                the members you want to get the stats from"""
        )

        if ctx.testing:
            try:
                reload(testing)
            except Exception as e:
                await self.bot.testing_error(module=testing, error=e)
                ctx.testing = False
        do = testing if ctx.testing else rtfm

        try:
            await do.command(ctx=ctx).stats(member=member)

        except:
            if ctx.testing:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(rtfm_extension(bot))


#
############
