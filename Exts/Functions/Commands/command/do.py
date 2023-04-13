############
#
from logging import getLogger
from statcord import Client
from Classes import ShakeBot, ShakeContext, MISSING

logger = getLogger('command')
########
#
class command_event():
    def __init__(self, ctx: ShakeContext, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.ctx: ShakeContext = ctx
        try:
            self.api = Client(bot=self.bot, token=self.bot.config.statcord.key)
        except:
            self.api = MISSING
        else:
            self.api.start_loop()
    
    async def __await__(self):
        self.ctx.done = False
        if not self.api is MISSING:
            self.api.command_run(self.ctx)
        
        query = """
            WITH insert AS (INSERT INTO commands (id, type) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING)
            UPDATE commands SET used_commands = used_commands+1 WHERE id = $1;
        """
        
        if not self.ctx.command in ("stats", "help",):
            await self.bot.pool.execute(query, self.ctx.guild.id, 'guild')
            await self.bot.pool.execute(query, self.bot.user.id, 'global')
            if self.ctx.author: 
                await self.bot.pool.execute(query, self.ctx.author.id, 'user')
        
        logger.info(f'{self.ctx.guild.id} > {self.ctx.author.id} (\"@{self.ctx.author}\"): {self.ctx.command}'+(' (failed)' if self.ctx.command_failed else ''))

#
############