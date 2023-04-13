import discord
from typing import Union, Optional
from Classes import ShakeBot, ShakeContext, ShakeEmbed
from discord import VoiceChannel, TextChannel, StageChannel, ForumChannel, CategoryChannel
CHANNELS = Union[VoiceChannel, TextChannel, StageChannel, ForumChannel, CategoryChannel]

class command():
    def __init__(self, ctx, channel: Optional[CHANNELS]) -> None:
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.channel: CHANNELS = channel or ctx.author.voice.channel


    async def __await__(self):
        if not self.channel.user_limit:
            self.channel.user_limit = "Infinite"

        embed = ShakeEmbed.default(
            title=f"{self.channel.name} Info",
            description=f"""
                Here is some info about {self.channel.mention}"
                🆔 **Channel ID:** `{self.channel.id}`
                🌀 **Channel Type:** {self.channel.type}""",
        )
        embed.add_field(name=f"📰 Name", value=f"{self.channel.name}")
        embed.add_field(name=f"📃 Category", value=f"{self.channel.category}")
        embed.add_field(name=f"🔉 Audio Bitrate", value=f"{round((self.channel.bitrate)/1000)} Kilo")
        embed.add_field(name=f"🔢 Channel Position", value=f"{self.channel.position+1}")
        embed.add_field(name=f"👤 Member Limit", value=f"{self.channel.user_limit}")
        embed.add_field(name=f"📆 Created On", value=f"<t:{round(self.channel.created_at.timestamp())}:D>")

        if self.ctx.guild.icon:
            embed.set_thumbnail(url=self.ctx.guild.icon)
        await self.ctx.smart_reply(embed=embed)