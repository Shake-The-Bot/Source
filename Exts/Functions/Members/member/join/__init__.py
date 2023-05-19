############
#
from discord import Member
from . import member_join, testing
from importlib import reload
from Classes import ShakeBot, Testing
from discord.ext.commands import Cog
########
#
class on_member_join(Cog):
    def __init__(self, bot):
        self.bot: ShakeBot = bot
        try:
            reload(member_join)
        except:
            pass

    @Cog.listener()
    async def on_member_join(self, member: Member):
        test = any(x.id in set(self.bot.cache['testing'].keys()) for x in [member, member.guild])
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                test = False
        do = testing if test else member_join

        try:
            await do.Event(member=member, bot=self.bot).__await__()
    
        except:
            if test:
                raise Testing
            raise

    
async def setup(bot: ShakeBot): 
    await bot.add_cog(on_member_join(bot))
#
############