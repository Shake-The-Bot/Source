############
#
from importlib import reload
from typing import Optional

from discord import Guild, TextChannel
from discord.ext.commands import Cog, GuildConverter, TextChannelConverter

from Classes import ShakeBot, Testing

from . import guild_join, testing


########
#
class on_guild_join(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(guild_join)
        except:
            pass

    @Cog.listener()
    async def on_guild_join(self, guild: Guild, channel: Optional[TextChannel] = None):
        test = guild.id in set(self.bot.testing.keys())

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
        do = testing if test else guild_join

        try:
            guild = await GuildConverter().convert(self, str(guild))
            channel = (
                await TextChannelConverter().convert(self, str(channel))
                if channel
                else None
            )
            await do.Event(guild=guild, channel=channel, bot=self.bot).__await__()

        except:
            if test:
                raise Testing
            raise


async def setup(bot: ShakeBot):
    await bot.add_cog(on_guild_join(bot))


#
############
