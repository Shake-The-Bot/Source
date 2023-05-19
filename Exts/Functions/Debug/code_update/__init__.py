############
#
from importlib import reload
from Classes import ShakeBot, ShakeContext
from . import code_update
from watchdog.observers import Observer
from discord.ext.commands import Cog
########
#
class on_code_update(Cog):
    def __init__(self, bot: ShakeBot):
        try:
            reload(code_update)
        except:
            pass

        self.bot: ShakeBot = bot
        self.handler = code_update.Handler(self.bot)
        self.watchdog = False
        self.observer = None
        self.start()

    def start(self):
        if self.watchdog:
            return
        
        self.observer = Observer()
        self.observer.schedule(self.handler, '.', recursive=True)
        self.observer.start()

        self.watchdog = True
    
    def stop(self):
        if not self.watchdog:
            return
        
        self.observer.stop()
        self.observer.join()
        self.observer = None

        self.watchdog = False

    async def cog_unload(self):
        self.stop()
    

async def setup(bot: ShakeBot): 
    await bot.add_cog(on_code_update(bot))
#
############