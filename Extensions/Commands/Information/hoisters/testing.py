from discord import Member

from Classes import Format, ShakeCommand, ShakeEmbed, _
from Classes.accessoires import ListMenu, ListPageSource

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
            name=f'{Format.codeblock(" " + str(self.items.index(item) + 1) + ". ")} {Format.codeblock(item)} [{Format.italics(str(item.id))}]',
            value=f'{Format.bold("➜")} {Format.codeblock(item.nick)} {item.mention}',
            inline=False,
        )
