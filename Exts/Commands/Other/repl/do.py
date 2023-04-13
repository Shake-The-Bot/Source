############
#
from io import BytesIO
from textwrap import indent
from time import time
from discord import HTTPException
from hmac import new
from base64 import b64encode
from Classes import ShakeBot, ShakeContext
from os import urandom as _urandom
import hashlib
########
#
def getrandbits(k):
    if k < 0:
        raise ValueError('number of bits must be non-negative')
    numbytes = (k + 7) // 8                       # bits / 8 and rounded up
    x = int.from_bytes(_urandom(numbytes), 'big')
    return x >> (numbytes * 8 - k) 

def random_token(id_):
    id_ = b64encode(str(id_).encode()).decode()
    time_ = b64encode(
        int.to_bytes(int(time.time()), 6, byteorder="big")
    ).decode()
    randbytes = bytearray(getrandbits(8) for _ in range(10))
    hmac_ = new(randbytes, randbytes, hashlib.md5).hexdigest()
    return f"{id_}.{time_}.{hmac_}"

def cleanup_code(content: str) -> str:
    """Automatically removes code blocks from the code."""
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])
    return content.strip("` \n")

class repl_command():
    def __init__(self, ctx, code: str, env):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.code = code
        self.env = env

    def sanitize(self, s):
        return s.replace('`', '′')

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
            'guild': self.ctx.message.guild, 'author': self.ctx.message.author, "__last__": self.env
        })

        if self.code.startswith('```py'): self.code = self.code[5:]
        self.code = self.code.strip('`').strip()
        _code = """
async def func():
    try:
{}
    finally:
        self.env.update(locals())
""".format(indent(self.code, ' ' * 6))

        _eval_start = time() * 1000

        try:
            exec(_code, self.env)
            output = await self.env['func']()
            if output is None: output = ''
            elif not isinstance(output, str): output = f'\n{repr(output) if output else str(output)}\n'
            else: output = f'\n{output}\n'
        except Exception as e:
            await self.ctx.message.add_reaction(self.bot.emojis.hook)
            output = f'\n{type(e).__name__}: {e}\n'
        _eval_end = time() * 1000
        self.code = self.code.split('\n')
        s = ''
        for i, line in enumerate(self.code):
            s += '>>> ' if i == 0 else '... '
            s += line + '\n'
        _eval_time = _eval_end - _eval_start
        message = f'{s}{output}# {_eval_time:.3f}ms'
        try:
            await self.ctx.smart_reply(f'```py\n{self.sanitize(message)}```')
        except HTTPException:
            paste = await self.bot.dump(message)
            await self.ctx.smart_reply(f'Repl Ergebnisse: <{paste}>')

        # env.update(globals())

        # body = cleanup_code(self.code)
        # stdout = io.StringIO()
        # token = random_token(self.bot.user.id)

        # to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        # try:
        #     exec(to_compile, env)
        # except Exception as e:
        #     return await self.ctx.smart_reply(f"```py\n{e.__class__.__name__}: {e}\n```")

        # func = env["func"]
        # try:
        #     with redirect_stdout(stdout):
        #         ret = await func()
        #     if ret is not None:
        #         ret = str(ret).replace(self.bot.http.token, token)
        # except Exception:
        #     value = stdout.getvalue()
        #     value = value.replace(self.bot.http.token, token)
        #     return await self.send(f"```py\n{value}{traceback.format_exc()}\n```")
        
        # value = stdout.getvalue()
        # value = value.replace(self.bot.http.token, token)
        # with contextlib.suppress(discord.Forbidden, discord.HTTPException):
        #         await self.ctx.message.add_reaction(self.bot.emojis.hook)

        # if ret is None:
        #     if value:
        #         await self.ctx.smart_reply(f"```py\n{value}\n```")
        # else:
        #     self._last_result = ret
        #     await self.ctx.smart_reply(f"```py\n{value}{ret}\n```")