############
#
from discord import Member, VoiceState
from importlib import reload
from . import do
from discord.ext import commands
########
#
class on_voice_state_update(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState,):
        if member.bot: 
            return
        if self.bot.dev:
            reload(do)
        return await do.voice_state_update_event(bot=self.bot, member=member, before=before, after=after).__await__()


async def setup(bot):
    await bot.add_cog(on_voice_state_update(bot))
#
############
