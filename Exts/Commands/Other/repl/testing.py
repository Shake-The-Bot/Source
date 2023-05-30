############
#
import hashlib
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT
from base64 import b64encode
from contextlib import redirect_stderr, redirect_stdout, suppress
from hmac import new
from inspect import isawaitable
from io import BytesIO, StringIO
from os import urandom as _urandom
from re import I, escape, sub
from textwrap import indent
from time import time
from traceback import format_exc
from types import FunctionType
from typing import Any

from discord import Forbidden, HTTPException
from discord.utils import maybe_coroutine

from Classes import MISSING, FormatTypes, ShakeBot, ShakeContext, TextFormat

mcb = lambda t: TextFormat.format(t, type=FormatTypes.multicodeblock)


########
#
def getrandbits(k):
    if k < 0:
        raise ValueError("number of bits must be non-negative")
    numbytes = (k + 7) // 8  # bits / 8 and rounded up
    x = int.from_bytes(_urandom(numbytes), "big")
    return x >> (numbytes * 8 - k)


def random_token(author):
    id_ = b64encode(str(author).encode()).decode()
    time_ = b64encode(int.to_bytes(int(time()), 6, byteorder="big")).decode()
    randbytes = bytearray(getrandbits(8) for _ in range(10))
    hmac_ = new(randbytes, randbytes, hashlib.md5).hexdigest()
    return f"{id_}.{time_}.{hmac_}"


def stdoutable(code: str, output: bool = False):
    content = code.split("\n")
    s = ""
    for i, line in enumerate(content):
        s += ("..." if output else ">>>") + " "
        s += line + "\n"
    return s


def safe_output(ctx: ShakeContext, input_: str) -> str:
    """Hides the bot's token from a string."""
    token = ctx.bot.http.token
    return sub(escape(token), random_token(ctx.author.id), input_, I)


def async_compile(source, filename, mode):
    return compile(source, filename, mode, flags=PyCF_ALLOW_TOP_LEVEL_AWAIT, optimize=0)


def cleanup(content: str) -> str:
    """Automatically removes code blocks from the code."""
    starts = ("py", "js")
    for start in starts:
        i = len(start)
        if content.startswith(f"```{start}"):
            content = content[3 + i :]
    if content.startswith(f"```"):
        content = content[3]
    content = content.strip("`").strip()
    return content


async def maybe_await(coro):
    for i in range(2):
        if isawaitable(coro):
            coro = await coro
        else:
            return coro
    return coro


def get_syntax_error(e):
    """Format a syntax error to send to the user.

    Returns a string representation of the error formatted as a codeblock.
    """
    if e.text is None:
        return "{0.__class__.__name__}: {0}".format(e)
    return "{0.text}{1:>{0.offset}}\n{2}: {0}".format(e, "^", type(e).__name__)


class command:
    def __init__(self, ctx, code: str, env, last):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.code = code
        self.last: Any = last
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
                "_": self.last,
            }
        )

    async def __await__(self):
        if not self.code:
            if not self.ctx.message.attachments:
                return await self.ctx.smart_reply("Nothing to evaluate.")

            atch = self.ctx.message.attachments[0]
            if not atch.filename.endswith(".txt"):
                return await self.ctx.smart_reply(
                    "File to evaluate must be a text document."
                )

            buf = BytesIO()
            await atch.save(buf, seek_begin=True, use_cached=False)
            self.code = buf.read().decode()

        stdout = StringIO()
        stderr = StringIO()
        cleaned = cleanup(self.code)

        if cleaned in ["exit()", "quit", "exit"]:
            self.env.clear()
            return await self.ctx.smart_reply("eval geleert")

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
                await self.ctx.send(mcb(get_syntax_error(e)))
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
                self.env["_"] = result
            elif stdouted or stderred:
                msg = "{}\n{}".format(stdouted, stderred)
        finally:
            end = time() * 1000
            completed = end - start

        final = safe_output(self.ctx, str(msg))
        final += f"\n\n# {completed:.3f}ms"

        try:
            await self.ctx.smart_reply(f"```py\n{final}```")
        except HTTPException:
            paste = await self.bot.dump(final)
            await self.ctx.smart_reply(f"Repl Ergebnisse: <{paste}>")
