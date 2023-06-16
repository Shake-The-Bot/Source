from discord import Member

from Classes import ShakeCommand, ShakeEmbed, TextFormat, _
from Classes.pages import ListMenu, ListPageSource

############
#


class command(ShakeCommand):
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
            return await self.ctx.chat(embed=embed)

        source = List(
            self.ctx, members, _("Here are all members with a nick, sorted by name.")
        )

        menu = ListMenu(source=source, ctx=self.ctx)

        if not await menu.setup():
            raise
        await menu.send(ephemeral=True)


class List(ListPageSource):
    def add_field(self, embed: ShakeEmbed, item: Member):
        embed.add_field(
            name=f'{TextFormat.codeblock(" " + str(self.items.index(item) + 1) + ". ")} {TextFormat.codeblock(item)} [{TextFormat.italics(str(item.id))}]',
            value=f'{TextFormat.bold("➜")} {TextFormat.codeblock(item.nick)}',
        )
