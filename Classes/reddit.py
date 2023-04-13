import asyncpraw
from asyncpraw.models import Subreddit, Submission
from random import choice
from time import time
from discord import Guild
from typing import TYPE_CHECKING
from collections import deque
from Classes.helpful import MISSING
from Classes.secrets.configuration import Config
config = Config('config.toml')

if TYPE_CHECKING:
    from Classes import __version__
    from Classes.helpful import ShakeContext
    from bot import ShakeBot
else:
    from discord.ext.commands import Context as ShakeContext, Bot as ShakeBot
    __version__ = MISSING
       
class Reddit:
    def __init__(self):
        self.posts = set()
        self.reddit = asyncpraw.Reddit(client_id=config.reddit.client_id, client_secret=config.reddit.client_secret, username=config.reddit.username, password=config.reddit.password, user_agent="Shake/{}".format(__version__),)
    
    async def __await__(self, ctx: ShakeContext):
        self.ctx: ShakeContext = ctx
        self.bot: ShakeBot = ctx.bot
        self.guild: Guild = ctx.guild
        self.guild_posts = ctx.bot.cached_posts.setdefault(ctx.guild.id, deque(maxlen=1000))
        await self.prepare()
    
    async def prepare(self):
        if not bool(len(self.posts)):
            pass
            return
        
        for post in self.posts:
            pass

    async def create(self, ctx, subreddits):
        subs: Subreddit = await self.reddit.subreddit('+'.join(subreddits), fetch=False)
        posts = [
            post async for post in subs.new(limit=25) if not post.over_18 and not post in self.guild_posts
        ]
        for post in posts:
            self.posts.add(post)
        return posts

    @classmethod
    def expire(self, post: Submission):
        self.guild_posts.add(post)

    async def get_post(self, ctx: ShakeContext, subreddit):
        if not bool(len(self.posts)):
            await self.create(ctx, subreddit)

        print(1, time())
        for post in self.posts:
            if post in self.guild_posts:
                continue
            print(2, time())
            self.expire(ctx, post)
            return post
        
        post = choice(list(await self.create(ctx, subreddit)))
        self.expire(ctx, post)
        return post
        