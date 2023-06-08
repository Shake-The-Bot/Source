############
#
from typing import NamedTuple
from json import loads
from Classes import CodeError, ShakeBot
from .models import ProductDataType, _currency
from typing import List, Dict
from datetime import datetime
from Classes.useful import MISSING
########
#
OFFERS_QUERY = "\n    query catalogQuery($productNamespace: String!, $offerId: String!, $locale: String, $country: String!, $includeSubItems: Boolean!) {\n  Catalog {\n    catalogOffer(namespace: $productNamespace, id: $offerId, locale: $locale) {\n      title\n      id\n      namespace\n      description\n      effectiveDate\n      expiryDate\n      isCodeRedemptionOnly\n      keyImages {\n        type\n        url\n      }\n      seller {\n        id\n        name\n      }\n      productSlug\n      urlSlug\n      url\n      tags {\n        id\n      }\n      items {\n        id\n        namespace\n      }\n      customAttributes {\n        key\n        value\n      }\n      categories {\n        path\n      }\n      price(country: $country) {\n        totalPrice {\n          discountPrice\n          originalPrice\n          voucherDiscount\n          discount\n          currencyCode\n          currencyInfo {\n            decimals\n          }\n          fmtPrice(locale: $locale) {\n            originalPrice\n            discountPrice\n            intermediatePrice\n          }\n        }\n        lineOffers {\n          appliedRules {\n            id\n            endDate\n            discountSetting {\n              discountType\n            }\n          }\n        }\n      }\n    }\n    offerSubItems(namespace: $productNamespace, id: $offerId) @include(if: $includeSubItems) {\n      namespace\n      id\n      releaseInfo {\n        appId\n        platform\n      }\n    }\n  }\n}\n"
PRODUCT_REVIEWS_QUERY = "\n            query productReviewsQuery($sku: String!) {\n                OpenCritic {\n                    productReviews(sku: $sku) {\n                        id\n                        name\n                        openCriticScore\n                        reviewCount\n                        percentRecommended\n                        openCriticUrl\n                        award\n                        topReviews {\n                            publishedDate\n                            externalUrl\n                            snippet\n                            language\n                            score\n                            author\n                            ScoreFormat {\n                                id\n                                description\n                            }\n                            OutletId\n                            outletName\n                            displayScore\n                        }\n                    }\n                }\n            }\n        "
########
#
class OfferData(NamedTuple):
    namespace: str
    offer_id: str
########
#
class EpicGamesStoreAPI:
    def __init__(self, bot: ShakeBot, locale="en-US", country="US"):
        self._session = bot.session
        self.locale = locale
        self.country = country

    async def __await__(self) -> List[ProductDataType]:

        epicgamesgames: List[Dict[str, str]] = list(
            sorted(
                filter(lambda p: p.get('promotions') and (slug := p.get('productSlug')) != '[]' and self.get_product(slug), self.get_free_games()['data']['Catalog']['searchStore']['elements']),
                key=lambda p: p['title']
            )
        )

        def _thumbnail(p):
            if bool(images := [image['url'] for image in p['keyImages'] if image['type'] == 'Thumbnail']):
                return images[0]
            return None

        games = []
        for i, product in enumerate(epicgamesgames, 1):
            slug = product.get('productSlug')
            data = self.get_product(slug)
            reviews = self.get_product_reviews(product_sku='EPIC_'+slug)

            currently = product['promotions']['promotionalOffers']
            

            offers = self.get_offers_data(*[OfferData(page['namespace'], page['offer']['id']) for page in data['pages'] if (offer := page.get('offer')) is not None and offer.get('id', None)])
            for offer in offers:
                offerdata = offer['data']['Catalog']['catalogOffer']
                originaldiscountPrice = offerdata["price"]["totalPrice"]["discountPrice"]
                price_with_currency = offerdata['price']['totalPrice']['fmtPrice']['originalPrice']
                originalPrice = offerdata['price']['totalPrice']['originalPrice']

            if not originaldiscountPrice == 0:
                continue

            image = sorted([page['data']['hero']['backgroundImageUrl'] for page in data['pages'] if page['data']['hero'].get('backgroundImageUrl', None)], key=len)[0]

            if currently and product['price']['totalPrice']['discountPrice'] == 0: 
                promotion = currently[0]['promotionalOffers'][0] # Promotion is active.
            elif currently: 
                promotion = currently[0]['promotionalOffers'][0] # Promotion is active.
            else: 
                continue

            start = datetime.fromisoformat(promotion['startDate'][:-1]) if promotion else MISSING
            end = datetime.fromisoformat(promotion['endDate'][:-1]) if promotion else MISSING
            id = product['id']
            title = product['title']
            description = product['description']
            publisher = product['seller']['name']
            url = f"https://store.epicgames.com/en-US/p/{product['productSlug']}"
            launcher = f"<com.epicgames.launcher://store/p/{product['productSlug']}>"
            currency = _currency.get((cr:=product['price']['totalPrice']['currencyCode']), cr)
            thumbnail = _thumbnail(product)

            games.append(
                ProductDataType(
                    id=id, title=title, description=description,
                    price=originalPrice, currency=currency, price_with_currency=price_with_currency,
                    thumbnail=thumbnail, image=image,
                    url=url, launcher=launcher,
                    publisher=publisher, reviews=reviews, store='epicgames',
                    start=start, end=end
                )
            )
        return games

    def get_product(self, slug: str) -> dict: #
        """Returns a product's data by slug.

        :param slug: Product's slug.
        """
        return self._make_api_query(
            f'/content/products/{slug}', method='GET', use_locale=True
        )

    def get_free_games(self, allow_countries: str = None) -> dict:
        if allow_countries is None:
            allow_countries = self.country
        api_uri = ('https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale={}&country={}&allowCountries={}')
        api_uri = api_uri.format(self.locale, self.country, allow_countries)
        data = self._session.get(api_uri).json()
        self._get_errors(data)
        return data

    def get_offers_data(self, *offers: OfferData, should_calculate_tax: bool = False, include_sub_items: bool = False) -> dict:
        return self._make_graphql_query(
            OFFERS_QUERY,
            {}, *[{
                'productNamespace': offer.namespace, 'offerId': offer.offer_id, 'lineOffers': [{'offerId': offer.offer_id,'quantity': 1}], 
                'calculateTax': should_calculate_tax,'includeSubItems': include_sub_items
            } for offer in offers]
        )

    def get_product_reviews(self, product_sku: str) -> dict:
        try:
            return self._make_graphql_query(PRODUCT_REVIEWS_QUERY, sku=product_sku)
        except:
            raise CodeError('There are no reviews for this product, or the given sku ({}) is incorrect.'.format(product_sku))

    def _make_api_query(self, endpoint: str, method: str, use_locale: bool = False, **variables) -> dict:
        func = getattr(self._session, method.lower())
        base_url = 'https://store-content.ak.epicgames.com'
        base_url += '/api' if not use_locale else f'/api/{self.locale}'
        response = func(base_url + endpoint, data=variables)
        if response.status_code == 404:
            return False
            raise CodeError(f'Page with endpoint {endpoint} was not reachable')
        response = response.json()
        self._get_errors(response)
        return response

    def _make_graphql_query(self, query_string, headers={}, *multiple_query_variables, **variables) -> dict:
        if not multiple_query_variables:
            variables.update({'locale': self.locale, 'country': self.country})
            response = self._session.post('https://graphql.epicgames.com/graphql', json={'query': query_string, 'variables': variables}, headers=headers).json()
        else:
            data = []
            for variables in multiple_query_variables:
                variables_ = {'locale': self.locale, 'country': self.country,}
                variables_.update(variables)
                data.append({'query': query_string, 'variables': variables_})
            response = self._session.post('https://graphql.epicgames.com/graphql', json=data, headers=headers).json()
        self._get_errors(response)
        return response

    @staticmethod
    def _get_errors(resp): #
        r = []
        if not isinstance(resp, list):
            r.append(resp)
        for response in r:
            if response.get('errors'):
                error = response['errors'][0]
                if not error['serviceResponse']:
                    raise CodeError(error['message'], service_response=error)
                service_response = loads(error['serviceResponse'])
                if isinstance(service_response, dict):
                    if service_response['errorCode'].endswith('not_found'):
                        raise CodeError(service_response['errorMessage'], service_response['numericErrorCode'], service_response)
                elif isinstance(service_response, str):
                    if service_response == 'not found':
                        raise CodeError('The resource was not found, No more data provided by Epic Games Store.')