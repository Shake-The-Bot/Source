from typing import Optional

from discord import Forbidden, HTTPException, TextChannel

from Classes import ShakeCommand, _

############
#


class command(ShakeCommand):
    async def setup(self, channel: Optional[TextChannel], react: bool):
        if not channel:
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
            query = """INSERT INTO aboveme (channel_id, guild_id, react) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING"""
            await connection.execute(query, channel.id, self.ctx.guild.id, react)

        await self.ctx.chat(
            _("The Aboveme-Game is succsessfully setup in {channel}").format(
                channel=channel.mention
            )
        )


#
############
