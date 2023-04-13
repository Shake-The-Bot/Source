############
#
from typing import List, Dict, Set
from importlib import reload
from apscheduler.triggers.cron import CronTrigger
from tweepy import API, OAuthHandler, StreamingClient
from Classes import ShakeBot
from zoneinfo import ZoneInfo
from . import twitter
from asyncio import run
from Classes.i18n import _
from discord.ext import commands
########
#

class Listener(StreamingClient):
    def __init__(self, bot, bearer_token, *, return_type=..., wait_on_rate_limit=True):
        super().__init__(bearer_token, wait_on_rate_limit=wait_on_rate_limit)
        self.bot = bot

    async def on_tweet(self, status):
        if self.bot.dev:
            reload(twitter)
        uri = f"https://twitter.com/{status.user.screen_name}/status/{status.id_str}"
        await twitter.event(bot=self.bot, status=status, uri=uri).__await__()
        return

    def on_status(self, status):
        run(self.on_tweet(status))
        

class on_tweet(commands.Cog):
    def __init__(self, bot: ShakeBot):
        self.bot: ShakeBot = bot
        self.bot.twitter: API = API(OAuthHandler(consumer_key=self.bot.config.twitter.api_key, consumer_secret=self.bot.config.twitter.api_key_secret, access_token=self.bot.config.twitter.access_token, access_token_secret=self.bot.config.twitter.access_token_secret))
        stream = Listener(bot, bearer_token=self.bot.config.twitter.bearer_token)
        #users = [str(self.bot.twitter.get_user(screen_name=user).id) for user in self.bot.config.twitter.users]
        #stream.filter(threaded=True)
	
async def setup(bot: ShakeBot): 
	await bot.add_cog(on_tweet(bot))
#
############