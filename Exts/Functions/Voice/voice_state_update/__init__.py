############
#
from importlib import reload

from discord import Member, VoiceState
from discord.ext.commands import Cog

from Classes import ShakeBot, Testing

from . import testing, voice_state_update


########
#
class on_voice_state_update(Cog):
    def __init__(self, bot: ShakeBot) -> None:
        self.bot: ShakeBot = bot
        try:
            reload(voice_state_update)
        except:
            pass

    @Cog.listener()
    async def on_voice_state_update(
        self,
        member: Member,
        before: VoiceState,
        after: VoiceState,
    ):
        if member.bot:
            return

        test = any(
            x.id in set(self.bot.testing.keys())
            for x in [
                getattr(before, "channel", None),
                getattr(after, "channel", None),
                member.guild,
            ]
            if x is not None
        )

        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical(
                    "Could not load {name}, will fallback ({type})".format(
                        name=testing.__file__, type=e.__class__.__name__
                    )
                )
                test = False
        do = testing if test else voice_state_update

        try:
            await do.Event(
                bot=self.bot, member=member, before=before, after=after
            ).__await__()

        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_voice_state_update(bot))


#
############
