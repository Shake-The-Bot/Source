from typing import Any, Dict
from datetime import datetime

_currency = {
    'EUR': '€',
    'USD': '$'
}

class ProductDataType(object):
	id: str
	title: str
	description: str
	publisher: str
	url: str
	launcher: str
	price: float
	price_with_currency: str
	reviews: dict
	thumbnail: str
	image: str
	store: str
	currency: str
	start: datetime
	end: datetime

	def __init__(
		self, 
		id: str, title: str, description: str,
		price: float, currency: str, price_with_currency: str,
		thumbnail: str, image: str,
		url: str, launcher: str,
		publisher: str, reviews: dict, store: str,
		start: datetime, end: datetime,
	) -> None:
		self.__data: Dict[str, Any] = {
			'id': id, 'title': title, 'description': description, 'price_with_currency': price_with_currency, 'price': price, 
			'currency': currency, 'thumbnail': thumbnail, 'image': image, 
			'url': url, 'launcher': launcher,  'publisher': publisher, 'reviews': reviews, 'store': store, 
			'start': start, 'end': end
		}
		self.format()

	def _setattr(self) -> None:
		for key, value in self.__data.items():
			setattr(self, key, value)
	
	def format(self):
		return self._setattr()

	@property
	def data(self):
		return self.__data