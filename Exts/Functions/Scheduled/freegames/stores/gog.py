############
#
import requests
from .models import ProductDataType
from typing import List, Dict
from Classes import ShakeBot
########
#
class GogStoreAPI:
    def __init__(self, bot: ShakeBot, locale="en-US", country="US"):
        self._session = bot.session
        self.locale = locale
        self.country = country

    async def __await__(self) -> List[ProductDataType]:
        data: List[Dict[str, str]] = self.get_free_games()	
        goggames: List[Dict[str, str]] = list(
            sorted(
                filter(lambda p: p['isGame'] and p['type'] == 2, [product for product in data['products']]), # and p['price']['isDiscounted']
                key=lambda p: p['title']
            )
        )
        games = []
        for i, product in enumerate(goggames, 1):
            title = product['title']
            type = product['type']
            slug = product['slug']
            demo = product['type'] == 1
            url = product['url']
            currency = product['price']['symbol']
            description = product['description']
            image = sorted([image['url'] for image in product['images']], key=len)[0]

            reviews = None
            image = None
            originalPrice = None
            publisher = None
            launcher = None
            start = None
            end = None
            thumbnail = None
            games.append(ProductDataType(
                store='gog', id=id, title=title, reviews=reviews, image=image, description=description, price=originalPrice, 
                publisher=publisher, url=url, launcher=launcher, start=start,
                currency=currency, end=end, thumbnail=thumbnail, 
            ))
            pass
        return games

    def get_free_games(self) -> dict:
        """Returns the games from "Free Games" section in the Steam Store."""
        endpoint = 'https://www.gog.com/games/ajax/filtered?mediaType=game&sort=popularity&price=free'
        # name = game['title']
        # link = game['url']
        return requests.get(endpoint).json()