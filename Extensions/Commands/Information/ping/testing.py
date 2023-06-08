############
#
from discord import ButtonStyle, PartialEmoji, ui

from Classes import ShakeBot, ShakeContext, ShakeEmbed, _


########
#
class command:
    def __init__(self, ctx: ShakeContext):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        embed = ShakeEmbed.default(
            self.ctx,
            title=_("Pong! 🏓"),
        )
        embed.add_field(
            name=_("Discord Gateway"),
            inline=True,
            value="> **{}**ms".format(round(self.bot.latency * 1000)),
        )
        embed.add_field(
            name=_("Client Latency"), inline=True, value="> **{}**ms".format(0)
        )

        #       pings = []
        # number = 0

        # typing_start = time.monotonic()
        # await ctx.typing()
        # typing_end = time.monotonic()
        # typing_ms = (typing_end - typing_start) * 1000
        # pings.append(typing_ms)

        # start = time.perf_counter()
        # message = await ctx.send("🏓 pong!")
        # end = time.perf_counter()
        # message_ms = (end - start) * 1000
        # pings.append(message_ms)

        # latency_ms = self.bot.latency * 1000
        # pings.append(latency_ms)

        # postgres_start = time.perf_counter()
        # await self.bot.db.fetch("SELECT 1")
        # postgres_end = time.perf_counter()
        # postgres_ms = (postgres_end - postgres_start) * 1000
        # pings.append(postgres_ms)

        # for ms in pings:
        #     number += ms
        # average = number / len(pings)

        # await asyncio.sleep(0.7)

        # await message.edit(
        #     content=re.sub(
        #         "\n *",
        #         "\n",
        #         f"\n{constants.WEBSITE} **| `Websocket ═╣ "
        #         f"{round(latency_ms, 3)}ms{' ' * (9 - len(str(round(latency_ms, 3))))}`** "
        #         f"\n{constants.TYPING_INDICATOR} **| `Typing ════╣ "
        #         f"{round(typing_ms, 3)}ms{' ' * (9 - len(str(round(typing_ms, 3))))}`**"
        #         f"\n:speech_balloon: **| `Message ═══╣ "
        #         f"{round(message_ms, 3)}ms{' ' * (9 - len(str(round(message_ms, 3))))}`**"
        #         f"\n{constants.POSTGRE_LOGO} **| `Database ══╣ "
        #         f"{round(postgres_ms, 3)}ms{' ' * (9 - len(str(round(postgres_ms, 3))))}`**"
        #         f"\n:infinity: **| `Average ═══╣ "
        #         f"{round(average, 3)}ms{' ' * (9 - len(str(round(average, 3))))}`**",
        #     )
        # )

        await self.ctx.chat(embed=embed, view=Link("https://discordstatus.com/"))


class Link(ui.View):
    def __init__(self, link):
        super().__init__()
        self.add_item(
            ui.Button(
                emoji=PartialEmoji(
                    name="\N{PERSONAL COMPUTER}",
                ),
                label=_("Discord Status"),
                url=link,
            )
        )


#
############
