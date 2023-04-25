############
#
from io import BytesIO, StringIO
from textwrap import indent
from time import time
from typing import Any
from discord import HTTPException, Forbidden
from hmac import new
from base64 import b64encode
from contextlib import redirect_stdout, suppress
from Classes import ShakeBot, ShakeContext, MISSING
from os import urandom as _urandom
from traceback import format_exc
import hashlib
########
#
def getrandbits(k):
    if k < 0:
        raise ValueError('number of bits must be non-negative')
    numbytes = (k + 7) // 8                                         # bits / 8 and rounded up
    x = int.from_bytes(_urandom(numbytes), 'big')
    return x >> (numbytes * 8 - k) 

def random_token(id_):
    id_ = b64encode(str(id_).encode()).decode()
    time_ = b64encode(
        int.to_bytes(int(time()), 6, byteorder="big")
    ).decode()
    randbytes = bytearray(getrandbits(8) for _ in range(10))
    hmac_ = new(randbytes, randbytes, hashlib.md5).hexdigest()
    return f"{id_}.{time_}.{hmac_}"

def printable(code: str, output: bool = False):
    content = code.split('\n')
    s = ''
    for i, line in enumerate(content):
        s += ('...' if output else '>>>') + ' '
        s += line + '\n'
    return s

def cleanup(content: str) -> str:
    """Automatically removes code blocks from the code."""
    starts = ('py', 'js')
    for start in starts:
        i = len(start)
        if content.startswith(f'```{start}'): 
            content = content[3+i:]
    if content.startswith(f'```'): 
        content = content[3]
    content = content.strip('`').strip()
    return content

class command():
    def __init__(self, ctx, code: str, env, last):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.code = code
        self.last: Any = last
        self.env = env


    async def __await__(self):
        if not self.code:
            if not self.ctx.message.attachments:
                return await self.ctx.smart_reply('Nothing to evaluate.')

            atch = self.ctx.message.attachments[0]
            if not atch.filename.endswith('.txt'):
                return await self.ctx.smart_reply('File to evaluate must be a text document.')

            buf = BytesIO()
            await atch.save(buf, seek_begin=True, use_cached=False)
            self.code = buf.read().decode()
            
        if self.code == 'exit()':
            self.env.clear()
            return await self.ctx.smart_reply('eval geleert')

        
        self.env.update({
            'self': self, 'bot': self.bot, 'ctx': self.ctx,
            'guild': self.ctx.guild, 'message': self.ctx.message, 'channel': self.ctx.message.channel,
            'guild': self.ctx.message.guild, 'author': self.ctx.message.author, "__last__": self.env,
            '_': self.last
        })

        
        content = cleanup(self.code)
        code = """
async def func():
    try:
{}
    finally:
        self.env.update(locals())
""".format(indent(content, ' ' * 8)).strip()
        printed = printable(content)
        stdout = StringIO()
        try:
            with redirect_stdout(stdout):
                exec(code, self.env)
        except Exception as e:
            await self.ctx.smart_reply(f"```py\n{e.__class__.__name__}: {e}\n```")
            return

        token = random_token(self.bot.user.id)
        
        start = time() * 1000
        try:
            
            with redirect_stdout(stdout):
                func = self.env['func']
                ret = await func()
        except Exception as err:
            with suppress(Forbidden, HTTPException):
                await self.ctx.message.add_reaction(self.bot.emojis.cross)
            await self.ctx.smart_reply(f"```py\n{printed}\n{err.__class__.__name__}: {err}\n```") #format_exc()
            return
        finally:
            end = time() * 1000
            completed = end - start

            value = stdout.getvalue()
            value = value.replace(self.bot.http.token, token)

        if ret is not None:
            if not isinstance(ret, str): 
                ret = str(repr(ret))
            ret = printable(ret, True)
            ret = '\n'+ret+'\n'.replace(self.bot.http.token, token)

        with suppress(Forbidden, HTTPException):
            await self.ctx.message.add_reaction(self.bot.emojis.hook)
        
        final = f"{printed}\n{value}{ret if ret else ''}\n# {completed:.3f}ms".replace('`', '′').replace(self.bot.http.token, token)

        try:
            await self.ctx.smart_reply(f'```py\n{final}```')
        except HTTPException:
            paste = await self.bot.dump(final)
            await self.ctx.smart_reply(f'Repl Ergebnisse: <{paste}>')

        if ret:
            return ret