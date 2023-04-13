############
#
from discord import PartialEmoji, Member
from importlib import reload
from Classes import ShakeContext
from zlib import decompressobj
from io import BytesIO
from re import compile
from . import rtfm
from os import path
from Classes.i18n import _, locale_doc
from discord import app_commands, Interaction
from discord.ext import commands

########
#
class rtfm_extension(commands.Cog):
    """
    rtfm_cog
    """
    def __init__(self, bot) -> None: 
        self.bot = bot
        self.bot.build_rtfm_lookup_table = self.build_rtfm_lookup_table


    @property
    def display_emoji(self) -> str: 
        return str(PartialEmoji(name='\N{BOOKS}'))


    def category(self) -> str: 
        return "information"

    async def build_rtfm_lookup_table(self):
        cache = {}
        for key, page in rtfm.RTFM_PAGE_TYPES.items():
            cache[key] = {}
            async with self.bot.session.get(page + "/objects.inv") as resp:
                if resp.status != 200: 
                    raise RuntimeError("RTFM-Nachschlagetabelle kann nicht erstellt werden. Versuche es später erneut.")
                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)
        self.bot._rtfm_cache = cache


    def parse_object_inv(self, stream, url):
        result = {}
        inv_version = stream.readline().rstrip()
        if inv_version != "# Sphinx inventory version 2": raise RuntimeError("Invalid objects.inv file version.")
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]
        line = stream.readline()
        if "zlib" not in line: raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")
        entry_regex = compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match: continue
            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result: continue
            if directive == "std:doc": subdirective = "label"
            if location.endswith("$"): location = location[:-1] + name
            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""
            if projname == "discord.py": key = key.replace("discord.ext.commands.", "").replace("discord.", "")
            result[f"{prefix}{key}"] = path.join(url, location)
        return result


    async def rtfm_slash_autocomplete(self, interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not hasattr(self.bot, '_rtfm_cache'):
            await interaction.response.autocomplete([])
            await self.build_rtfm_lookup_table()
            return []

        if not current:
            return []

        if len(current) < 3:
            return [app_commands.Choice(name=current, value=current)]

        assert interaction.command is not None
        key = interaction.command.name
        matches = rtfm.finder(current, self.bot._rtfm_cache[key])[:10]
        return [app_commands.Choice(name=m, value=m) for m in matches]


    @commands.hybrid_group(name='rtfm')
    @app_commands.guild_only()
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def rtfm(self, ctx: ShakeContext, entity: str) -> None:
        _(
            """View objects from certain documentation.

            RTFM is internet slang for the phrase "read the damn manual"."""
        )
        if self.bot.dev:
            reload(rtfm)
        await rtfm.rtfm_command(ctx, 'stable', entity)
        return

    
    @rtfm.command(name="discordpy")
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def discordpy(self, ctx: ShakeContext, entity: str):
        _(
            """View certain objects from the official discord.py documentation.
            
            Parameters
            -----------
            entity: Optional[str]
                the entity to look for in the documentation"""
        )
        if self.bot.dev:
            reload(rtfm)
        await rtfm.rtfm_command(ctx=ctx, key="latest", obj=entity).__await__()
        return


    @rtfm.command(name="python")
    @app_commands.autocomplete(entity=rtfm_slash_autocomplete)
    @locale_doc
    async def python(self, ctx: ShakeContext, entity: str):
        _(
            """View certain objects from official python documentation. 

            RTFM is internet slang for the phrase "read the damn manual".
            
            Parameters
            -----------
            entity: Optional[str]
                the entity to look for in the documentation"""
        )
        if self.bot.dev:
            reload(rtfm)
        await rtfm.rtfm_command(ctx=ctx, key="python", obj=entity).__await__()
        return


    @rtfm.command(name="stats")
    @locale_doc
    async def stats(self, ctx: ShakeContext, member: commands.Greedy[Member] = None):
        _(
            """View the members stats of the rtfm command.
            
            Parameters
            -----------
            member: Greedy[Member]
                the members you want to get the stats from"""
        )
        if self.bot.dev:
            reload(rtfm)
        return await rtfm.rtfm_command(ctx=ctx, member=member).do_sub()

class SphinxObjectFileReader:
    BUFSIZE = 16 * 1024
    def __init__(self, buffer): self.stream = BytesIO(buffer)
    def readline(self): return self.stream.readline().decode("utf-8")
    def skipline(self): self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0: break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")

async def setup(bot): 
    await bot.add_cog(rtfm_extension(bot))
#
############

