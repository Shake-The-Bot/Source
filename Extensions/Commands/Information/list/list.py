############
#
from discord import PartialEmoji

from Classes import MISSING, ShakeCommand, _
from Classes.pages import ListMenu, ListPageSource


########
#
class command(ShakeCommand):
    async def __await__(self):
        guilds = sorted(self.bot.guilds, key=lambda g: len(g.members))
        menu = ListMenu(
            ctx=self.ctx,
            source=PageSource(
                ctx=self.ctx,
                items=guilds,
                current=self.ctx.guild,
                title=_("Current Guilds"),
                description=_(
                    "I'm currently in `{guilds}` guilds & this one is in top **{current}**."
                ).format(guilds=len(guilds), current=guilds.index(self.ctx.guild) + 1),
            ),
        )
        await menu.setup()
        await menu.send(ephemeral=True)


class PageSource(ListPageSource):
    def add_field(self, embed, item):
        tick = (
            str(PartialEmoji(name="left", id=1033551843210579988))
            if self.kwargs.get("current", MISSING) == item
            else ""
        )
        embed.add_field(
            name="` {index}. ` \N{EM DASH} {name} {tick}".format(
                index=self.items.index(item) + 1, name=item.name, tick=tick
            ),
            value=_(
                "**ID**: `{id}` **OWNER**: `{owner}` **MEMBERS**: `{members}`"
            ).format(id=item.id, owner=item.owner, members=len(item.members)),
            inline=False,
        )


#
############
