############
#
from typing import Any, Tuple, Union

from discord import Member

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _, bold, codeblock, italics
from Classes.pages import ListMenu, ListPageSource


########
#
class command:
    def __init__(self, ctx: ShakeContext):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot

    async def __await__(self):
        members = list(
            sorted(
                [member for member in self.ctx.guild.members if bool(member.nick)],
                key=lambda m: m.nick,
            )
        )

        if not bool(members):
            embed = ShakeEmbed().to_error(
                ctx=self.ctx, description=_("There are no members with a nick.")
            )
            return await self.ctx.smart_reply(embed=embed)

        source = List(
            self.ctx, members, _("Here are all members with a nick, sorted by name.")
        )

        menu = ListMenu(source=source, ctx=self.ctx)

        if not await menu.setup():
            raise
        await menu.send()


class List(ListPageSource):
    def add_field(self, embed: ShakeEmbed, item: Member):
        embed.add_field(
            name=f'{codeblock(" " + str(self.items.index(item) + 1) + ". ")} {codeblock(item)} [{italics(str(item.id))}]',
            value=f'{bold("➜")} {codeblock(item.nick)}',
        )
