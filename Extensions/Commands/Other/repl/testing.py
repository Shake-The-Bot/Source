############
#
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
from textwrap import indent
from time import time
from traceback import format_exc
from types import FunctionType
from typing import Any

from discord import HTTPException, Message

from Classes import (
    ShakeBot,
    ShakeContext,
    TextFormat,
    async_compile,
    cleanup,
    get_syntax_error,
    maybe_await,
    safe_output,
)

########
#


class command:
    def __init__(self, ctx, code: str, env, last):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.code = code
        self.last: Any = last
        ref = self.ctx.message.reference

        self.env: dict[str, Any] = env
        self.env.update(
            {
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
                    except SyntaxError:
                        raise
                    else:
                        executor = eval

        formed = """
async def func():
    try:
{}
    finally:
        self.env.update(locals())
""".format(
            indent(cleaned, " " * 8)
        ).strip()

        if executor is None:
            try:
                code = async_compile(formed, "<repl session>", "exec")
            except SyntaxError as e:
                await self.ctx.send(TextFormat.multicodeblock(get_syntax_error(e)))
                return

        # self.env["_"] =

        # stdouted = stdoutable(cleaned)
        msg = ""

        start = time() * 1000

        try:
            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    if executor is None:
                        result = FunctionType(code, self.env)()
                    else:
                        result = executor(code, self.env)
                    result = await maybe_await(result)
        except:
            stdouted = stdout.getvalue()
            stderred = stderr.getvalue()

            msg = "{}{}{}".format(stdouted, stderred, format_exc())
        else:
            stdouted = stdout.getvalue()
            stderred = stderr.getvalue()
            if result is not None:
                msg = "{}\n{}\n{}".format(
                    result,
                    stdouted,
                    stderred,
                )
                self.env["__"] = result
            elif stdouted or stderred:
                msg = "{}\n{}".format(stdouted, stderred)
        finally:
            end = time() * 1000
            completed = end - start

        final = safe_output(self.ctx, str(msg))
        final += f"\n\n# {completed:.3f}ms"

        try:
            await self.ctx.chat(f"```py\n{final}```", reference=None)
        except HTTPException:
            paste = await self.bot.dump(final)
            await self.ctx.chat(f"Repl Ergebnisse: <{paste}>", reference=None)
