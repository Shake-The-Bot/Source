############
#
from discord import Member, VoiceState
from importlib import reload
from . import voice_state_update, testing
from Classes import Testing, ShakeBot
from discord.ext.commands import Cog
########
#
class on_voice_state_update(Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState,):
        if member.bot: 
            return
        
        test = any(x.id in list(self.bot.tests.keys()) for x in (getattr(before, 'channel', None), getattr(after, 'channel', None), member.guild) if x is not None)

        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else voice_state_update

        try:
            await do.event(bot=self.bot, member=member, before=before, after=after).__await__()
    
        except:
            if test:
                raise Testing
            raise
        


async def setup(bot: ShakeBot):
    await bot.add_cog(on_voice_state_update(bot))
#
############
