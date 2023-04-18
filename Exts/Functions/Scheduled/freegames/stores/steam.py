############
#
import itertools
import requests
from Classes import ShakeBot
from .models import ProductDataType, _currency
from typing import List, Dict
from enum import Enum
########
#
class SteamCategory(Enum):
    CATEGORY_Single_player = "2"  #: Single-player games
    CATEGORY_Multi_player = "1"  #: Multi-player games
    CATEGORY_PvP = "49"  #: PvP games
    CATEGORY_Online_PvP = "36"  #: Online PvP games
    CATEGORY_Co_op = "9"  #: Co-op games
    CATEGORY_Online_Co_op = "38"  #: Online Co-op games
    CATEGORY_Steam_Trading_Cards = "29"  #: Steam Trading Cards games

    @staticmethod
    def join_categories(*categories_list) -> str:
        return '|'.join([category.value for category in categories_list])

    def __add__(self, other):
        if isinstance(other, SteamCategory):
            return self.join_categories(self, other)
        raise NotImplementedError

class SteamStoreAPI:
    def __init__(self, bot: ShakeBot, locale="en-US", country="DE"):
        self._session = bot.session
        self.locale = locale
        self.country = country
        self.params = {
            "filter": "free",
            "cc": country,  # DE: Landcode für Deutschland (ändern Sie diesen Wert, um Spiele in einem anderen Land abzurufen)
            "l": "german"  # german: Sprache (ändern Sie diesen Wert, um Spiele in einer anderen Sprache abzurufen)
        }

    async def __await__(self) -> List[ProductDataType]:
        datas: List[Dict[str, str]] = self.get_free_games()
        steamgames: List[Dict[str, str]] = list(
            sorted(
                #filter(lambda p: p, [product for category in data.get('featured_win', {}) for product in category['items'] if 'free_games' in category['name'].lower()]),
                filter(lambda p: p, datas),
                key=lambda p: p['name']
            )
        )
        games = []
        for i, product in enumerate(steamgames, 1):
            _data = self.get_product(product['id'])
            if not _data or not _data.get('success', None):
                continue
            data: dict = _data['data']
            if not (data.get('is_free', False)) or not (price := data.get('price_overview', None)):
                continue
            id = product['id']
            title = product['name']
            url = 'https://s.team/a/{id}/'.format(id=id)
            description = data['short_description']
            launcher = 'steam://store/{id}'.format(id=id)
            price_with_currency = price['initial_formatted']
            originalPrice = price['initial_formatted']
            publisher = ', '.join(data['publishers'])
            image = product['large_capsule_image']

            reviews = None
            end = None
            start = None
            currency = _currency.get((cr:=price['currency']), cr)
            thumbnail = None
            games.append(ProductDataType(
                store='steam', id=id, title=title, reviews=reviews, image=image, description=description,
                price=originalPrice, currency=currency, price_with_currency=price_with_currency,
                publisher=publisher, url=url, launcher=launcher, start=start,
                end=end, thumbnail=thumbnail, 
            ))
        return games

    def get_free_games(self) -> dict:
        """Returns the games from "Free Games" section in the Steam Store."""
        endpoint = 'https://store.steampowered.com/api/featuredcategories'
        # 'https://store.steampowered.com/api/featuredcategories' 
        # 'https://api.steampowered.com/ISteamApps/GetAppList/v2'
        request = requests.get(endpoint).json()
        specials = request['specials']['items']
        top_sellers = request['top_sellers']['items']
        new_releases = request['new_releases']['items']
        items = list(
            itertools.chain(
                specials, top_sellers, new_releases
            )
        )
        return [product for product in items if (product['discounted']) and (product['final_price'] == 0)]

    def get_product(self, _id) -> dict:
        endpoint = f'https://store.steampowered.com/api/appdetails?appids={_id}'
        request = requests.get(endpoint)
        if request.status_code == 400:
            return None
        return (request.json() or {}).get(str(_id), None)
