from typing import Optional

from discord import Forbidden, HTTPException, TextChannel

from Classes import ShakeBot, ShakeContext, _

############
#


class command:
    def __init__(
        self,
        ctx: ShakeContext,
        channel: Optional[TextChannel],
        hardcore: bool,
    ):
        self.bot: ShakeBot = ctx.bot
        self.ctx: ShakeContext = ctx
        self.channel: Optional[TextChannel] = channel
        self.hardcore: bool = hardcore

    async def __await__(self):
        if not self.channel:
            try:
                channel = await self.ctx.guild.create_text_channel(
                    name="aboveme", slowmode_delay=5
                )
            except (
                HTTPException,
                Forbidden,
            ):
                await self.ctx.smart_reply(
                    _(
                        "The Aboveme-Game couldn't setup because I have no permissions to do so."
                    )
                )
                return False
            self.channel = channel

        async with self.ctx.db.acquire() as connection:
            query = """INSERT INTO aboveme (channel_id, guild_id, hardcore) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"""
            await connection.execute(
                query, self.channel.id, self.ctx.guild.id, self.hardcore
            )

        await self.ctx.smart_reply(
            _("The Aboveme-Game is succsessfully setup in {channel}").format(
                channel=self.channel.mention
            )
        )


#
############
