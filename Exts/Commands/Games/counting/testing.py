from typing import Optional

from discord import Forbidden, HTTPException, TextChannel

from Classes import ShakeBot, ShakeContext, _

############
#


class command:
    def __init__(
        self,
        ctx: ShakeContext,
        channel: TextChannel,
        goal: Optional[int],
        hardcore: bool,
        only_numbers: bool,
    ):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.channel: Optional[TextChannel] = channel
        self.goal: Optional[int] = goal
        self.hardcore: bool = hardcore
        self.numbers: bool = only_numbers

    async def __await__(self):
        if not self.channel:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="counting", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                await self.ctx.smart_reply(
                    _(
                        "The Counting-Game couldn't setup because I have no permissions to do so."
                    )
                )
                return False
            self.channel = channel

        async with self.ctx.db.acquire() as connection:
            query = """INSERT INTO counting (channel_id, guild_id, goal, hardcore, numbers) VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING"""
            await connection.execute(
                query,
                self.channel.id,
                self.ctx.guild.id,
                self.goal,
                self.hardcore,
                self.numbers,
            )

        await self.ctx.smart_reply(
            _("The Counting-Game is succsessfully setup in {channel}").format(
                channel=self.channel.mention
            )
        )


#
############
