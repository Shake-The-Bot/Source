
from importlib import reload
from sys import modules
from typing import Union, Tuple, List
from inspect import getfile
from time import time
from Classes import ShakeBot, ShakeContext
from watchdog.events import FileSystemEventHandler, DirModifiedEvent, FileModifiedEvent
from os import path
from watchdog.observers import Observer
from discord.ext.commands import Cog, ExtensionNotLoaded, Command
from discord import Message


class Handler(FileSystemEventHandler):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bot.cache
        self.tasks = self.history = dict()

    def interval(self, event, seconds: int = 1):
        form = f'{type(event).__name__}:{event.src_path}'

        if form not in self.tasks:
            self.tasks[form] = time()
            return True
        else:
            memory = self.tasks[form]
            if seconds > (time() - memory):
                return False
            else:
                self.tasks[form] = time()
                return True

    def add_test(self,):
        pass

    def on_moved(self, event):
        pass

    def on_created(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]):
        if self.interval(event, seconds=5):
            self.bot.loop.create_task(self.modified(event))

    def testing(self, path: str):
        cases = set([
            'pycache' in path, 
            path.endswith('.tmp'),
            not path.endswith('.py'),
        ])
        if any(x for x in cases):
            return False
        if not any(_ in path for _ in ['Functions', 'Commands']):
            return False
        if not path.endswith('testing.py') and not path.endswith('__init__.py'):
            return False
        return True
    
    def active(self, source: str):
        parts = str(source).split('/')[1:]
        name, category = (parts[-2], parts[1:3])

        testings = dict()
        for command, ctx in self.bot.cache['tests'].items():
            cog: Cog = getattr(command, 'cog', getattr(command, 'binding', None))
            if not cog:
                continue
            parts = getfile(cog.__class__).removesuffix('.py').split('/')
            testings[tuple(parts[parts.index('Exts')+1:parts.index('Exts')+3]) + tuple(parts[-2])] = ctx

        if not tuple(category)+tuple(name) in list(testings.keys()):
            return None, None

        ctx: ShakeContext = testings[tuple(category)+tuple(name)]
        reloadable = '.'.join(parts[parts.index('Exts'):]).removesuffix('.py')
        return ctx, reloadable

    async def modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]):
        """A private background function to reload `testing.py` **command** files when they are used in ptb cases"""
        if not isinstance(event, FileModifiedEvent):
            return

        if not self.testing(event.src_path):
            return

        ctx, reloadable = self.active(event.src_path)
        if any(x is None for x in [ctx, reloadable]):
            return


        message = f'`[Watchdog]` <a:processing:1108969075041894460> :: Auto-reloading `{reloadable}`'
        if reloadable in self.history:
            sent: Message = self.history[reloadable]
            await sent.edit(content=message)
        else:
            sent = self.history[reloadable] = await ctx.channel.send(content=message)

        content = None
        try:
            try:
                await self.bot.reload_extension(reloadable)
            except ExtensionNotLoaded:
                await self.bot.load_extension(reloadable)
            except:
                content = f'`[Watchdog]` Unknown extension {reloadable}'
            
        except Exception as ex:
            content=f'`[Watchdog]` Reloading `{reloadable}` failed: {ex}'
        else:
            content=f'`[Watchdog]` `{reloadable}` reloaded.'
        
        if not content is None:
            await sent.edit(content=content)

        # elif 'Classes' in reloadable:
        #     if reloadable in modules:
        #         reload(modules[reloadable])
        #     else:
        #         __import__(reloadable)