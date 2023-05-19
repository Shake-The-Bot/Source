############
#
from importlib import reload
from discord import Interaction
from Classes import ShakeBot, Testing
from . import interaction as _interaction, testing
from discord.ext.commands import Cog
########
#
class on_interaction(Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        try:
            reload(_interaction)
        except:
            pass

    @Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        
        test = any(x.id in set(self.bot.cache['testing'].keys()) for x in [interaction.user, interaction.guild, interaction.channel])
        
        if test:
            try:
                reload(testing)
            except Exception as e:
                self.bot.log.critical('Could not load {name}, will fallback ({type})'.format(
                    name=testing.__file__, type=e.__class__.__name__
                ))
                test = False
        do = testing if test else _interaction

        try:
            await do.Event(bot=self.bot, interaction=interaction).__await__()
    
        except:
            if test:
                raise Testing
            raise



async def setup(bot: ShakeBot): 
    await bot.add_cog(on_interaction(bot))
#
############