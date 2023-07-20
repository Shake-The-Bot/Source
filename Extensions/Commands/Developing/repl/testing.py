import asyncio
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
from textwrap import indent
from time import time
from traceback import format_exc
from typing import Any

import aiohttp
import discord
from discord import HTTPException, Message

from Classes import (
    Format,
    ShakeCommand,
    ShakeEmbed,
    async_compile,
    cleanup,
    get_syntax_error,
    helpful,
    maybe_await,
    safe_output,
    stdoutable,
    useful,
)

############
#


class command(ShakeCommand):
    def __init__(self, ctx, code: str, env, last):
        super().__init__(ctx)
        self.code = code
        self.last: Any = last
        ref = self.ctx.message.reference

        self.env: dict[str, Any] = env
        self.env.update(
            {
                "aiohttp": aiohttp,
                "asyncio": asyncio,
                "discord": discord,
                "helpful": helpful,
                "useful": useful,
                "Format": Format,
                "self": self,
                "bot": self.bot,
                "ctx": self.ctx,
                "guild": self.ctx.guild,
                "message": self.ctx.message,
                "channel": self.ctx.channel,
                "author": self.ctx.message.author,
                "__last__": self.env,
                "__ref": ref.resolved
                if ref and isinstance(ref.resolved, Message)
                else None,
                "__": self.last,
            }
        )

    async def __await__(self):
        if not self.code:
            if not self.ctx.message.attachments:
                return await self.ctx.chat("Nothing to evaluate.")
            atch = self.ctx.message.attachments[0]
            if not atch.filename.endswith(".txt"):
                return await self.ctx.chat("File to evaluate must be a text document.")
            buf = BytesIO()
            await atch.save(buf, seek_begin=True, use_cached=False)
            self.code = buf.read().decode()

        stdout = StringIO()
        stderr = StringIO()
        cleaned = cleanup(self.code)

        if cleaned in ["exit()", "quit", "exit"]:
            self.env.clear()
            return await self.ctx.chat("eval geleert")

        executor = None
        if cleaned.count("\n") == 0:
            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    try:
                        code = async_compile(cleaned, "<repl session>", "eval")
                    except SyntaxError as e:
                        error = cleanup(safe_output(self.ctx, get_syntax_error(e)))
                        return await self.ctx.send(Format.multicodeblock(error))
                    else:
                        executor = eval

        formatted = stdoutable(cleaned)
        formed = """
async def func():
    try:
{}
    except:
        raise
    finally:
        self.env.update(locals())
""".format(
            indent(cleaned, "   " * 2)
        ).strip()

        if executor is None:
            try:
                with redirect_stdout(stdout):
                    with redirect_stderr(stderr):
                        code = async_compile(formed, "<repl session>", "exec")
                        exec(code, self.env)
            except SyntaxError as e:
                error = cleanup(safe_output(self.ctx, get_syntax_error(e)))
                return await self.ctx.send(Format.multicodeblock(error))

        start = time() * 1000
        exception = result = None
        try:
            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    if executor is None:
                        func = self.env["func"]
                        result = await func()
                    else:
                        awaiting = executor(code, self.env)
                        result = await maybe_await(awaiting)
        except:
            exception = format_exc()
            stdouted = stdout.getvalue()
            stderred = stderr.getvalue()

            msg = "{}{}{}".format(stdouted, stderred, exception)
        else:
            stdouted = stdout.getvalue()
            stderred = stderr.getvalue()
            if result is not None:
                self.env["__"] = result
            msg = "\n".join(str(_) for _ in (result, stdouted, stderred) if bool(_))

        finally:
            completed = time() * 1000 - start

        embed = ShakeEmbed()
        embed.title = f"Real-eval-print loop process done"
        embed.description = Format.multicodeblock(formatted, "py")
        embed.set_footer(text=f"{completed:.0f}ms")
        fields = {
            "Stdout": stdouted,
            "Stderr": stderred,
            "Results": result,
            "Exceptions": exception,
        }
        for name, value in fields.items():
            if bool(value):
                embed.add_field(
                    name=name,
                    inline=False,
                    value=Format.multicodeblock(
                        cleanup(safe_output(self.ctx, str(value).replace("`", "´"))),
                        "py",
                    ),
                )

        try:
            await self.ctx.send(embed=embed, reference=None)
        except HTTPException:
            paste = await self.bot.dump(cleaned(safe_output(self.ctx, str(msg))))
            await self.ctx.chat(f"Repl Ergebnisse: <{paste}>", reference=None)
