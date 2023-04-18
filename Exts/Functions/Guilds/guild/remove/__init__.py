############
#
from discord import Guild
from importlib import reload
from . import guild_remove, testing
from Classes import ShakeBot, Testing
from discord.ext.commands import Cog
########
#
class on_guild_remove(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        test = guild.id in list(self.bot.tests.keys())
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                ctx.testing = False
        do = testing if test else guild_remove

        try:
            await do.event(guild=guild, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_guild_remove(bot))
#
############