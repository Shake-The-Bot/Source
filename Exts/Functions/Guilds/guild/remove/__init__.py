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
class on_guild_remove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        if self.bot.dev:
            reload(do)
        return await do.guild_remove_event(guild=guild, bot=self.bot).__await__()
    
async def setup(bot): 
    await bot.add_cog(on_guild_remove(bot))
#
############