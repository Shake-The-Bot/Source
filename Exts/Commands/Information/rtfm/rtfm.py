############
#
from typing import Generator, Iterable, Optional, Callable, List
from re import escape, IGNORECASE, compile, sub
from Classes.i18n import _
from discord.ext import commands
from discord import Member
from typing import Callable, Iterable, Optional, TypeVar, Generator
from discord.abc import Messageable
from Classes import ShakeContext, ShakeBot, ShakeEmbed

T = TypeVar('T')
RTFM_PAGE_TYPES = {
    'stable': 'https://discordpy.readthedocs.io/en/stable',
    'stable-jp': 'https://discordpy.readthedocs.io/ja/stable',
    'latest': 'https://discordpy.readthedocs.io/en/latest',
    'latest-jp': 'https://discordpy.readthedocs.io/ja/latest',
    'python': 'https://docs.python.org/3',
    'python-jp': 'https://docs.python.org/ja/3',
}
########
#
class RtfmKey():
    """convert into a valid key"""
    @classmethod
    async def convert(cls, ctx: ShakeContext, argument: Optional[str] = None) -> List[str]:
        return argument if not argument is None and argument in RTFM_PAGE_TYPES else None

def finder(text: str, collection: Iterable[str], *, key: Optional[Callable[[str], str]] = ..., lazy: bool = True,) -> list[str]:
    suggestions: list[tuple[int, int, str]] = []
    text = str(text)
    pat = '.*?'.join(map(escape, text))
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

class rtfm_command():
    def __init__(self, ctx: commands.Context, key: RtfmKey = None, obj: str = None, member: List[Member] = None):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.member: List[Member] = member
        self.key = key
        self.obj: str = obj

    async def __await__(self):
        await self.ctx.defer()
        if self.obj is None: 
            return await self.ctx.smart_reply(RTFM_PAGE_TYPES[self.key])
        if not hasattr(self.bot, "_rtfm_cache"): 
            await self.bot.build_rtfm_lookup_table()
        obj = sub(r"^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", self.obj)
        if self.key.startswith("latest"):
            q = obj.lower()
            for name in dir(Messageable):
                if name[0] == "_": continue
                if q == name:
                    obj = f"abc.Messageable.{name}"
                    break
        cache = list(self.bot._rtfm_cache[self.key].items())
        matches = finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]
        if len(matches) == 0: 
            return await self.ctx.smart_reply(_("Couldn't find anything."))
        embed = ShakeEmbed.default(self.ctx, description = "\n".join(f"[`{key}`]({url})" for key, url in matches))
        await self.ctx.smart_reply(embed=embed)
        await self.bot.pool.execute("INSERT INTO rtfm (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET count = rtfm.count + 1;", self.ctx.author.id)
        return

    async def _member_stats(self, ctx: ShakeContext, member: List[Member], total_uses: int):
        embed = ShakeEmbed.default(self.ctx, )
        embed.set_author(
            name="RTFM Stats {prefix} {user_names}".format(
                prefix=self.bot.emojis.prefix, user_names=", ".join(member)
            ), icon_url=self.bot.user.display_avatar.url
        )
        query = "SELECT count FROM rtfm WHERE user_id=$1;"
        for m in member:
            record = await self.bot.pool.fetchrow(query, m.id)
            count = 0 if record is None else record["count"]
            embed.add_field(name=_("Uses"), value=count, inline=False)
            embed.add_field(name=_("Total", value=f"{count/total_uses:.0%} von {total_uses}"), inline=False)
        await ctx.smart_reply(embed=embed)
    
    async def do_sub(self):
        """Tells you stats about the ?rtfm command."""
        query = "SELECT SUM(count) AS total_uses FROM rtfm;"
        record = await self.bot.pool.fetchrow(query)
        total_uses: int = record["total_uses"]

        if self.member is not None:
            return await self._member_stats(self.ctx, self.member, total_uses)

        query = "SELECT user_id, count FROM rtfm ORDER BY count DESC LIMIT 10;"
        records = await self.bot.pool.fetch(query)
        output = []
        if total_uses is None: return await self.ctx.smart_reply("Keine Einträge")
        output.append(_("**Total uses**: {total_uses}").format(total_uses=total_uses))

        if records:
            output.append(_("**Top {top} member**:").format(top=len(records)))
            for rank, (user_id, count) in enumerate(records, 1):
                user = self.bot.get_user(user_id) or (await self.bot.fetch_user(user_id))
                if rank != 10:
                    output.append(f"{rank}\u20e3 {user}: {count}")
                else:
                    output.append(f"\N{KEYCAP TEN} {user}: {count}")

        await self.ctx.smart_reply("\n".join(output))
            
########
#


#
############