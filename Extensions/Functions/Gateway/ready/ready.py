############
#
from datetime import datetime

from discord.ext.commands import AutoShardedBot

from Classes import Format, ShakeBot, __version__


########
#
class Event:
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    async def __await__(self):
        if not hasattr(self.bot, "ready"):
            if hasattr(self.bot, "ready_shards"):
                ready = len(self.bot.ready_shards.added())
            else:
                ready = None

            info = "({guilds} server & {users} users) [version {version}]".format(
                guilds=len(self.bot.guilds),
                users=len(self.bot.users),
                version=str(__version__),
            )

            if isinstance(self.bot, AutoShardedBot):
                message = (
                    "{name} is successfully divided into {ready} of {all} shard(s)."
                )
            else:
                message = "{name} is ready"

            self.bot.log.info(
                Format.join(
                    message.format(
                        name=self.bot.user.name,
                        ready=ready,
                        all=len(getattr(self.bot, "shards", [])),
                    ),
                    info,
                )
            )

            self.bot.ready = True

        if not hasattr(self.bot, "boot"):
            self.bot.boot = datetime.now()


#
############
