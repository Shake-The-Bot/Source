############
#
from logging import getLogger

from Classes import ShakeBot, ShakeContext

log = getLogger("shake.commands")
########
#


class Event:
    def __init__(self, ctx: ShakeContext, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.ctx: ShakeContext = ctx

    async def __await__(self):
        # if not self.ctx.command in [
        #     "stats",
        #     "help",
        # ]:
        #     query = """
        #         WITH insert AS (INSERT INTO commands (id, type) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING)
        #         UPDATE commands SET used_commands = used_commands+1 WHERE id = $1;
        #     """
        #     await self.bot.pool.execute(query, self.ctx.guild.id, "guild")
        #     await self.bot.pool.execute(query, self.bot.user.id, "global")
        #     if self.ctx.author:
        #         await self.bot.pool.execute(query, self.ctx.author.id, "user")

        log.info(
            f'{self.ctx.guild.id} > {self.ctx.author.id} ("@{self.ctx.author}"): {self.ctx.command}'
            + (" (failed)" if self.ctx.command_failed else "")
        )
        # message = self.ctx.message
        # destination = None
        # if self.ctx.guild is None:
        #     destination = "Private Message"
        # else:
        #     destination = f"#{message.channel} ({message.guild})"

        # if self.ctx.interaction and self.ctx.interaction.command:
        #     content = f"/{self.ctx.interaction.command.qualified_name}"
        # else:
        #     content = message.content

        # log.info(f"{message.created_at}: {message.author} in {destination}: {content}")


#
############
