############
#
from typing import List, Set
from importlib import reload
from apscheduler.triggers.cron import CronTrigger
from Classes import ShakeBot
from zoneinfo import ZoneInfo
from .stores.gog import GogStoreAPI
from .stores.epicgames import EpicGamesStoreAPI
from .stores.steam import SteamStoreAPI
from .stores.models import ProductDataType
from . import freegames
from Classes import _
from discord.ext.commands import Cog
########
#
database_fake_products = [] # TODO

class on_freegame(Cog):
	def __init__(self, bot: ShakeBot):
		self.bot: ShakeBot = bot
		#self.bot.scheduler.add_job(self.freegames, CronTrigger(minute='10,40', timezone=ZoneInfo("Europe/Berlin")))

	async def freegames(self):

		old_games: Set = set(
			tuple(k) for k, v in (
				await self.bot.pool.fetchval(
					"SELECT games FROM freegames WHERE id = $1", self.bot.user.id
				) or {})
			.items()
		)

		new_games: List[ProductDataType] = list(
			await SteamStoreAPI().__await__() +  await EpicGamesStoreAPI().__await__() + await GogStoreAPI().__await__()
		)

		if not bool(valids := set(p for p in new_games if bool(p) and not p.id in old_games)):
			return False


		for guild in [self.bot.get_guild(guild_id) for guild_id in await self.bot.config_pool.fetch("SELECT guild_id FROM freegames")]:
			try:
				await self.on_freegame(guild=guild, games=valids)
			except Exception as e:
				self.bot.log.error('Coundn\'t send freegame to guild "{name}" ({id})'.format(name=guild.name, id=guild.id), exc_info=e)

		for game in new_games:
			old_games.add(str(game.id))

		await self.bot.pool.execute(
			"UPDATE freegames SET games = $2 WHERE id = $1", self.bot.user.id, old_games
		)

	async def on_freegame(self, games: Set[ProductDataType]):
		reload(freegames)
		return await freegames.freegames_Event(bot=self.bot, games=games).__await__()
	
async def setup(bot: ShakeBot): 
	await bot.add_cog(on_freegame(bot))
#
############