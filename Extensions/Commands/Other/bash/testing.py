############
#
from asyncio import (
    FIRST_COMPLETED,
    Semaphore,
    Task,
    TimeoutError,
    create_subprocess_shell,
    create_task,
    sleep,
    wait,
)
from asyncio.subprocess import DEVNULL, PIPE
from re import sub
from time import perf_counter
from typing import Optional

from discord import Message, Reaction, User
from discord.ext import commands

from Classes import ShakeBot, ShakeContext


########
#
class TextPaginator:
    __slots__ = ("ctx", "reactions", "_paginator", "current", "message", "update_lock")

    def __init__(
        self,
        ctx: ShakeContext,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> None:
        self._paginator = commands.Paginator(
            prefix=prefix, suffix=suffix, max_size=1950
        )
        self.current = 0
        self.message: Optional[Message] = None
        self.ctx = ctx
        self.update_lock = Semaphore(value=2)
        self.reactions = {
            "⏮": "first",
            "◀": "previous",
            "⏹": "stop",
            "▶": "next",
            "⏭": "last",
            "🔢": "choose",
        }

    @property
    def pages(self) -> list[str]:
        return self._paginator.pages

    @property
    def page_count(self) -> int:
        return len(self.pages)

    async def add_line(self, line: str) -> None:
        before = self.page_count
        if isinstance(line, str):
            self._paginator.add_line(line)
        else:
            for _line in line:
                self._paginator.add_line(_line)
        after = self.page_count
        if after > before:
            self.current = after - 1
        create_task(self.update())

    async def react(self) -> None:
        if self.message is None:
            raise Exception("May not be called before sending the message.")
        for emoji in self.reactions:
            await self.message.add_reaction(emoji)

    async def send(self) -> None:
        self.message = await self.ctx.chat(
            self.pages[self.current] + f"Page {self.current + 1} / {self.page_count}"
        )
        create_task(self.react())
        create_task(self.listener())

    async def update(self) -> None:
        if self.update_lock.locked():
            return

        async with self.update_lock:
            if self.update_lock.locked():
                await sleep(1)
            if not self.message:
                await sleep(0.5)
            else:
                await self.message.edit(
                    content=self.pages[self.current]
                    + f"Page {self.current + 1} / {self.page_count}"
                )

    async def listener(self) -> None:
        def check(reaction: Reaction, user: User) -> bool:
            return (
                user == self.ctx.author
                and self.message is not None
                and reaction.message.id == self.message.id
                and reaction.emoji in self.reactions
            )

        while not self.ctx.bot.is_closed():
            try:
                reaction, user = await self.ctx.bot.wait_for(
                    "reaction_add", check=check, timeout=120
                )
            except TimeoutError:
                if self.message is not None:
                    await self.message.delete()
                return
            action = self.reactions[reaction.emoji]
            if action == "first":
                self.current = 0
            elif action == "previous" and self.current != 0:
                self.current -= 1
            elif action == "next" and self.page_count != self.current + 1:
                self.current += 1
            elif action == "last":
                self.current = self.page_count - 1
            elif action == "stop":
                if self.message is not None:
                    await self.message.delete()
                return
            elif action == "choose":
                choose_msg = await self.ctx.chat(
                    "Bitte sende eine Nummer zwischen 1 und {max_pages}".format(
                        max_pages=self.page_count
                    )
                )

                def new_check(msg):
                    return (
                        msg.author.id == self.ctx.author.id
                        and msg.content.isdigit()
                        and 0 < int(msg.content) <= self.page_count
                    )

                try:
                    m = await self.ctx.bot.wait_for(
                        "message", check=new_check, timeout=30
                    )
                    await choose_msg.delete()
                except TimeoutError:
                    if self.message is not None:
                        await self.message.delete()
                    await self.ctx.chat("Hat zu lange gebracht. Abbruch.")
                    return
                self.current = int(m.content) - 1
            await self.update()


class command:
    def __init__(self, ctx, command: str):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.command = command

    async def __await__(self):
        pager = f"```sh\n$ {self.command}\n"
        process = await create_subprocess_shell(
            self.command, stdin=DEVNULL, stdout=PIPE, stderr=PIPE
        )
        tasks = {
            Task(process.stdout.readline()): process.stdout,
            Task(process.stderr.readline()): process.stderr,
        }
        buf = []
        time_since_last_update = perf_counter()
        written = False
        while process.returncode is None or not process.stdout.at_eof():
            done, pending = await wait(tasks, return_when=FIRST_COMPLETED)
            assert done
            for future in done:
                stream = tasks.pop(future)
                line = future.result().decode("utf-8")
                line = (
                    sub(r"\x1b[^m]*m", "", line).replace("``", "`\u200b`").strip("\n")
                )
                if line:  # not EOF
                    buf.append(line)
                    right_now = perf_counter()
                    if right_now > time_since_last_update + 0.5 or written is False:
                        if isinstance(buf, str):
                            pager += f">> {buf}\n\n"
                        else:
                            for _line in buf:
                                pager += f">> {_line}\n"
                        time_since_last_update = perf_counter()
                        buf = []
                        written = True
                tasks[Task(stream.readline())] = stream

        if buf:
            if isinstance(buf, str):
                pager += f">> {buf}\n\n"
            else:
                for _line in buf:
                    pager += (
                        f">> {_line}\n" if not buf[-1] == _line else f">> {_line}\n\n"
                    )
        pager = pager + f"[Exit code: {process.returncode}]\n```"
        await self.ctx.chat(pager)
