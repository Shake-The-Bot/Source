############
#
from importlib import reload
from contextlib import suppress
from .utils import systems
from discord import Message, Member, Forbidden, HTTPException, HTTPException
from asyncpg import Pool
from Classes import ShakeBot
########
#
class Event():
    def __init__(self, message: Message, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.message: Message = message
        
        
    async def await_level(self):
        level = systems.level.levelsystem(member=self.author, _object=self.message, bot=self.bot)
        if await level.__await__() is False:
            return False
        if getattr(level, 'up', None): 
            await self.message.channel.send(level.up)
        return True

    async def await_oneword(self):
        oneword = systems.oneword(member=self.author, message=self.message, bot=self.bot)
        if await oneword.__await__() is False:
            return False
        delete_message = oneword.do.get('delete_message', False)
        add_reaction = oneword.do.get('add_reaction', False)
        add_bad = oneword.do.get('add_bad_reaction', False)
        with suppress(Forbidden, HTTPException):
            if add_bad or add_reaction:
                await self.message.add_reaction('☑️' if add_reaction else self.bot.emojis.cross)
            if getattr(oneword, 'kwargs', None):
                await self.message.channel.send(**getattr(oneword, 'kwargs'), delete_after=10 if delete_message else None)
            if delete_message:
                await self.message.delete(delay=10)
        return True

    async def await_aboveme(self):
        aboveme = systems.aboveme(member=self.author, message=self.message, bot=self.bot)
        if await aboveme.__await__() is False:
            return False
        delete_message = aboveme.do.get('delete_message', False)
        add_reaction = aboveme.do.get('add_reaction', False)
        add_bad = aboveme.do.get('add_bad_reaction', False)
        with suppress(Forbidden, HTTPException):
            if add_bad or add_reaction:
                await self.message.add_reaction('☑️' if add_reaction else self.bot.emojis.cross)
            if getattr(aboveme, 'kwargs', None):
                await self.message.channel.send(**getattr(aboveme, 'kwargs'), delete_after=10 if delete_message else None)
            if delete_message:
                await self.message.delete(delay=10)
        return True

    async def await_counting(self):
        counting = systems.counting(member=self.author, message=self.message, bot=self.bot)
        if await counting.__await__() is False: 
            return False
        delete_message = counting.do.get('delete_message', False)
        add_reaction = counting.do.get('add_reaction', False)
        add_bad = counting.do.get('add_bad_reaction', False)
        add_warning = counting.do.get('add_warning_reaction', False)
        with suppress(Forbidden, HTTPException):
            if add_bad or add_reaction or add_warning:
                await self.message.add_reaction(('☑️' if  add_reaction else '⚠️') if (add_reaction or add_warning) else self.bot.emojis.cross)
            if getattr(counting, 'kwargs', None):
                await self.message.channel.send(**getattr(counting, 'kwargs'), delete_after=10 if delete_message else None)
            if delete_message:
                await self.message.delete(delay=10)
        return True
        

    async def __await__(self):
        self.author = self.message.author
        self.guild = self.message.guild
        if any([self.author.bot, not self.guild, not isinstance(self.author, Member)]): 
            return
        ctx = await self.bot.get_context(self.message)
        if not (ctx.valid and ctx.command): 
            self.db: Pool = await self.bot.get_pool(_id=self.message.guild.id)
            self.config: Pool = self.bot.config_pool
            reload(systems)
            if bool(await self.config.fetch("SELECT * FROM counting WHERE guild_id = $1 AND turn = $2", self.message.guild.id, True) or []): 
                counting = await self.await_counting()
            
            if bool(await self.config.fetch("SELECT * FROM aboveme WHERE guild_id = $1 AND turn = $2", self.message.guild.id, True) or []):
                aboveme = await self.await_aboveme()
            
            if bool(await self.config.fetch("SELECT * FROM oneword WHERE guild_id = $1 AND turn = $2", self.message.guild.id, True) or []):
                oneword = await self.await_oneword()
            
            if await self.config.fetchrow("""SELECT * FROM level WHERE guild_id = $1 AND turn = $2""", self.message.guild.id, True) or []: 
                if not any(x for x in [counting, aboveme, oneword]):
                    level_response = await self.await_level()
        return
#
############