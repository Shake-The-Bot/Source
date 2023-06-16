############
#
from io import BytesIO
from os import path
from re import IGNORECASE, compile, escape, sub
from typing import Callable, Iterable, List, Optional, TypeVar
from zlib import decompressobj

from discord import Member
from discord.abc import Messageable

from Classes import ShakeCommand, ShakeEmbed, Types, _

T = TypeVar("T")
########
#


class SphinxObjectFileReader:
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
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


async def build_rtfm_lookup_table(bot):
    cache = dict()
    for key, page in Types.RtfmPage.value.items():
        cache[key] = dict()
        async with bot.session.get(page + "/objects.inv") as resp:
            if resp.status != 200:
                raise RuntimeError(
                    "RTFM-Nachschlagetabelle kann nicht erstellt werden. Versuche es später erneut."
                )
            stream = SphinxObjectFileReader(await resp.read())
            cache[key] = parse_object_inv(stream, page)
    bot._rtfm_cache = cache


def parse_object_inv(stream, url):
    result = dict()
    line = stream.readline()
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
        result[f"{prefix}{key}"] = path.join(url, location)
    return result


def finder(
    text: str,
    collection: Iterable[str],
    *,
    key: Optional[Callable[[str], str]] = ...,
    lazy: bool = True,
) -> list[str]:
    suggestions: list[tuple[int, int, str]] = []
    text = str(text)
    pat = ".*?".join(map(escape, text))
    regex = compile(pat, flags=IGNORECASE)
    for item in collection:
        to_search = key(item) if key else item
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup: tuple[int, int, str]) -> tuple[int, int, str]:
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    if lazy:
        return (z for _, _, z in sorted(suggestions, key=sort_key))
    else:
        return [z for _, _, z in sorted(suggestions, key=sort_key)]


class command(ShakeCommand):
    async def __await__(self, key, obj: str = None):
        self.key = key
        self.obj: str = obj
        await self.ctx.defer()
        if self.obj is None:
            return await self.ctx.chat(Types.RtfmPage.value[self.key])
        if not hasattr(self.bot, "_rtfm_cache"):
            await self.bot.build_rtfm_lookup_table()
        obj = sub(r"^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", self.obj)
        if self.key.startswith("latest"):
            q = obj.lower()
            for name in dir(Messageable):
                if name[0] == "_":
                    continue
                if q == name:
                    obj = f"abc.Messageable.{name}"
                    break
        cache = set(self.bot._rtfm_cache[self.key].items())
        matches = finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]
        if len(matches) == 0:
            return await self.ctx.chat(_("Couldn't find anything."))
        embed = ShakeEmbed.default(
            self.ctx, description="\n".join(f"[`{key}`]({url})" for key, url in matches)
        )
        await self.ctx.chat(embed=embed)
        await self.bot.pool.execute(
            "INSERT INTO rtfm (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET count = rtfm.count + 1;",
            self.ctx.author.id,
        )
        return

    async def stats(self, member: List[Member] = None):
        """Tells you stats about the ?rtfm command."""
        self.member: List[Member] = member
        query = "SELECT SUM(count) AS total_uses FROM rtfm;"
        record = await self.bot.pool.fetchrow(query)
        total_uses: int = record["total_uses"]

        if self.member is not None:
            embed = ShakeEmbed.default(
                self.ctx,
            )
            embed.set_author(
                name="RTFM Stats {prefix} {user_names}".format(
                    prefix=self.bot.emojis.prefix, user_names=", ".join(self.member)
                ),
                icon_url=self.bot.user.display_avatar.url,
            )
            query = "SELECT count FROM rtfm WHERE user_id=$1;"
            for m in self.member:
                record = await self.bot.pool.fetchrow(query, m.id)
                count = 0 if record is None else record["count"]
                embed.add_field(name=_("Uses"), value=count, inline=False)
                embed.add_field(
                    name=_("Total", value=f"{count/total_uses:.0%} von {total_uses}"),
                    inline=False,
                )
            await self.ctx.chat(embed=embed)
            return

        query = "SELECT user_id, count FROM rtfm ORDER BY count DESC LIMIT 10;"
        records = await self.bot.pool.fetch(query)
        output = []
        if total_uses is None:
            return await self.ctx.chat("Keine Einträge")
        output.append(_("**Total uses**: {total_uses}").format(total_uses=total_uses))

        if records:
            output.append(_("**Top {top} member**:").format(top=len(records)))
            for rank, (user_id, count) in enumerate(records, 1):
                user = self.bot.get_user(user_id) or (
                    await self.bot.fetch_user(user_id)
                )
                if rank != 10:
                    output.append(f"{rank}\u20e3 {user}: {count}")
                else:
                    output.append(f"\N{KEYCAP TEN} {user}: {count}")

        await self.ctx.chat("\n".join(output))


#
############
