############
#
from typing import Optional
from discord import Guild, TextChannel
from importlib import reload
from . import do
from discord.ext.commands import GuildConverter, TextChannelConverter
from discord.ext import commands
########
#
class on_guild_join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild, channel: Optional[TextChannel] = None):
        if self.bot.dev:
            reload(do)
        guild = await GuildConverter().convert(self, str(guild))
        channel = await TextChannelConverter().convert(self, str(channel)) if channel else None
        return await do.guild_join_event(guild=guild, channel=channel, bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_guild_join(bot))
#
############