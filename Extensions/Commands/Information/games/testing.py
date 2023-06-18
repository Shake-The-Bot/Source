############
#
from unicodedata import name

from Classes import MISSING, ShakeCommand, ShakeContext, _
from Classes.accessoires import ListMenu, ListPageSource


########
#
class command(ShakeCommand):
    def __init__(self, ctx, characters):
        super().__init__(ctx)
        self.characters = characters

    async def __await__(self):
        filtered = set()
        source = PageSource(
            ctx=self.ctx,
            title=_("Charinfo Command"),
            group=None,
            items=[
                c
                for c in self.characters
                if c not in filtered and (filtered.add(c) or True)
            ],
            description="Format of Character-Information: \n**`\\UNICODE` \N{EM DASH} CHARACTERNAME \N{EM DASH} ` CHARACTER `**",
        )
        menu = ListMenu(ctx=self.ctx, source=source)
        await menu.setup()
        await menu.send(ephemeral=True)
        return


class PageSource(ListPageSource):
    def add_field(self, embed, item):
        embed.add_field(
            name="` {index}. ` \N{EM DASH} „{name}“".format(
                index=self.items.index(item) + 1, name=item
            ),
            inline=False,
            value="`\\U{0:>08}` \N{EM DASH} {1} \N{EM DASH} ` {2} `\n<http://www.fileformat.info/info/unicode/char/{0}>".format(
                format(ord(item), "x"), name(item, "Name not found."), item
            ),
        )


#
############
