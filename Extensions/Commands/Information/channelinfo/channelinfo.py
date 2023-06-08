from typing import Optional

from Classes import ShakeBot, ShakeContext, ShakeEmbed, channeltypes


class command:
    def __init__(self, ctx: ShakeContext, channel: Optional[channeltypes]) -> None:
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.channel: channeltypes = (
            channel or getattr(ctx.author.voice, "channel", None) or ctx.channel
        )

    async def __await__(self):
        embed = ShakeEmbed.default(
            title=f"{self.channel.name} Info",
            description=f"""
                Here is some info about {self.channel.mention}"
                🆔 **Channel ID:** `{self.channel.id}`
                🌀 **Channel Type:** {self.channel.type}""",
        )
        embed.add_field(name=f"📰 Name", value=f"{self.channel.name}")
        embed.add_field(name=f"📃 Category", value=f"{self.channel.category}")
        embed.add_field(
            name=f"🔉 Audio Bitrate", value=f"{round((self.channel.bitrate)/1000)} Kilo"
        )
        embed.add_field(name=f"🔢 Channel Position", value=f"{self.channel.position+1}")
        embed.add_field(
            name=f"👤 Member Limit", value=f"{self.channel.user_limit or 'Infinite'}"
        )
        embed.add_field(
            name=f"📆 Created On",
            value=f"<t:{round(self.channel.created_at.timestamp())}:D>",
        )

        if self.ctx.guild.icon:
            embed.set_thumbnail(url=self.ctx.guild.icon)
        await self.ctx.chat(embed=embed)
