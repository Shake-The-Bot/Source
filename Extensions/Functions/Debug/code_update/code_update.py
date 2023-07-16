from importlib import reload
from inspect import getfile
from re import findall
from sys import modules
from time import time

from discord.ext.commands import Cog, ExtensionNotLoaded
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler

from Classes import ShakeBot, ShakeContext


class Handler(FileSystemEventHandler):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bot.cache
        self.tasks = self.history = dict()

    def interval(self, event, seconds: int = 1):
        form = f"{type(event).__name__}:{event.src_path}"

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

    def add_test(
        self,
    ):
        pass

    def on_moved(self, event):
        pass

    def on_created(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent):
        if self.interval(event, seconds=10):
            self.bot.loop.create_task(self.modified(event))

    def utils(self, path: str):
        cases = set(
            [
                not "Classes" in path,
                path.endswith(".tmp"),
                not path.endswith(".py"),
            ]
        )
        if any(x for x in cases):
            return False
        return True

    def testing(self, path: str):
        cases = set(
            [
                "pycache" in path,
                path.endswith(".tmp"),
                not path.endswith(".py"),
            ]
        )
        if any(x for x in cases):
            return False
        if not any(_ in path for _ in ["Functions", "Commands"]):
            return False
        if not path.endswith("testing.py") and not path.endswith("__init__.py"):
            return False
        return True

    def is_active_test(self, source: str):
        parts = str(source).split("/")[1:]
        name, category = (parts[-2], parts[1:3])

        testings = dict()
        for command, ctx in self.bot.cache["tests"].items():
            cog: Cog = getattr(command, "cog", getattr(command, "binding", None))
            if not cog:
                continue
            parts = getfile(cog.__class__).removesuffix(".py").split("/")
            testings[
                tuple(
                    parts[parts.index("Extensions") + 1 : parts.index("Extensions") + 3]
                )
                + tuple(parts[-2])
            ] = ctx

        if not tuple(category) + tuple(name) in list(testings.keys()):
            return None, None

        ctx: ShakeContext = testings[tuple(category) + tuple(name)]
        reloadable = ".".join(parts[parts.index("Extensions") :]).removesuffix(".py")
        return ctx, reloadable

    async def modified(self, event: DirModifiedEvent | FileModifiedEvent):
        """A private background function to reload `testing.py` **command** files when they are used in public test build cases"""
        if not isinstance(event, FileModifiedEvent):
            return

        if self.testing(event.src_path):
            ctx, reloadable = self.is_active_test(event.src_path)
            if all([ctx is None, reloadable is None]):
                return

            try:
                messages = [message async for message in ctx.channel.history(limit=1)]
            except:
                last = None
            else:
                last = messages[0]

            last_content = None
            number = 0
            if last:
                if numbers := findall(r"\d+", last.content):
                    number = int("".join(map(str, numbers)))
                    last_content = last.content.removesuffix(f" ({number}x)")
                else:
                    last_content = last.content

            # message = f"`[Watchdog]` <a:processing:1108969075041894460> :: Auto-reloading `{reloadable}`"
            # sent = await ctx.channel.send(content=message)

            content = None
            try:
                try:
                    await self.bot.reload_extension(reloadable)
                except ExtensionNotLoaded:
                    return
                    # await self.bot.load_extension(reloadable)
                except:
                    content = f"`[Watchdog]` Unknown extension {reloadable}"

            except Exception as ex:
                content = f"`[Watchdog]` Reloading `{reloadable}` failed: {ex}"
            else:
                content = f"`[Watchdog]` `{reloadable}` reloaded."

            if (
                last_content
                and content == last_content
                and last.author == self.bot.user
            ):
                await last.edit(content=content + f" ({number+1}x)")
            else:
                await ctx.channel.send(content=content + f" ({number+1}x)")

        elif self.utils(event.src_path):
            parts = str(event.src_path).split("/")[1:]
            reloadable = ".".join(parts[parts.index("Classes") :]).removesuffix(".py")
            try:
                if reloadable in modules.keys():
                    reload(modules[reloadable])
                else:
                    __import__(reloadable)
            except (ImportError, SyntaxError):
                pass
        else:
            return
