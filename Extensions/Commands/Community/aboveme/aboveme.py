from typing import Dict, List, Optional

from discord import Forbidden, Guild, HTTPException, TextChannel

from Classes import ShakeCommand, ShakeContext, ShakeEmbed, TextFormat, UserGuild, _
from Classes.accessoires import ListPageSource, ShakePages

############
#


class Page(ListPageSource):
    def __init__(
        self,
        ctx: ShakeContext,
        title: str,
        items: Dict[Guild, int],
        description: str | None = ...,
        label: str | None = ...,
    ):
        self.from_dict: Dict[Guild, int] = items
        items = list(
            _
            for _ in dict(
                sorted(items.items(), key=lambda x: x[1], reverse=True)
            ).keys()
            if _
        )
        super().__init__(ctx, items, title, None, description, True, 10, label)

    async def format_page(self, menu, items: list[Guild]):
        embed = ShakeEmbed()
        embed.title = self.title
        embed.description = "\n".join(
            [
                "{} {}, {}".format(
                    TextFormat.bold("#" + str(items.index(item) + 1)),
                    TextFormat.codeblock(item.name),
                    TextFormat.bold(self.from_dict[item]),
                )
                for item in items
            ]
        )
        return embed, None


class command(ShakeCommand):
    async def score(self, type: str) -> None:
        try:
            type = UserGuild[type.lower()].value
        except KeyError:
            type = Guild
        is_guild = type == Guild
        async with self.bot.gpool.acquire() as connection:
            if is_guild:
                query = "SELECT guild_id, count FROM aboveme;"
            else:
                query = "SELECT user_id, SUM(CASE WHEN failed = false THEN 1 ELSE 0 END) AS count FROM abovemes GROUP BY user_id;"
                # highest = "SELECT user_id, MAX(count) AS highest FROM countings GROUP BY user_id;"
            counters: List[int, int] = await connection.fetch(query)

        items = {
            self.bot.get_guild(_id)
            if is_guild
            else await self.bot.get_user_global(_id): score
            for _id, score in counters
        }

        title = (
            TextFormat.italics(_("CURRENT SERVER SCORES"))
            if is_guild
            else TextFormat.italics(_("CURRENT USER SCORES"))
        )

        source = Page(
            self.ctx,
            title=title,
            items=items,
        )
        menu = ShakePages(source, self.ctx)
        await menu.setup()
        await menu.send(ephemeral=True)
        pass

    async def setup(self, channel: Optional[TextChannel], react: bool):
        if not channel or not channel in self.ctx.guild.text_channels:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="aboveme", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                await self.ctx.chat(
                    _(
                        "The Aboveme-Game couldn't setup because I have no permissions to do so."
                    )
                )
                return False
            channel = channel

        async with self.ctx.db.acquire() as connection:
            query = 'INSERT INTO aboveme (channel_id, guild_id, "react") VALUES ($1, $2, $3) ON CONFLICT DO NOTHING'
            await connection.execute(query, channel.id, self.ctx.guild.id, react)

        await self.ctx.chat(
            _("The Aboveme-Game is succsessfully setup in {channel}").format(
                channel=channel.mention
            )
        )


#
############
