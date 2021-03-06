import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TiendaEntel(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        response = session.get(
            'https://miportal.entel.cl/lista-productos?Nrpp=1000&'
            'format=json-rest')

        json_prepago = json.loads(response.text)

        records = json_prepago['response']['main'][2].get('records', None)

        if not records:
            records = json_prepago['response']['main'][1].get('records', None)

        for record in records:
            cell_id = record['attributes']['productId'][0]
            cell_url = 'https://miportal.entel.cl/personas/producto/Equipos/' \
                       + cell_id
            product_urls.append(cell_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        return cls._products_for_url(url, extra_args)

    @classmethod
    def _products_for_url(cls, url, extra_args=None, retries=5):
        print(url)
        session = session_with_proxy(extra_args)

        products = []

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        raw_json = soup.find(
            'div', {'id': 'productDetail'}).find('script').string

        if not raw_json:
            if retries:
                return cls._products_for_url(url, extra_args,
                                             retries=retries-1)
            else:
                raise Exception('JSON error')

        json_data = json.loads(raw_json)

        description = html_to_markdown(
            str(soup.find('div', 'details-description'))
        )

        for sku in json_data['renderSkusBean']['skus']:
            price_container = sku['skuPrice']
            if not price_container:
                continue

            price = Decimal(price_container).quantize(0)

            if sku['available']:
                stock = -1
            else:
                stock = 0

            sku_id = sku['skuId']

            pictures_container = []

            for view in json_data['skuViews']:
                if view['skuId'] == sku_id:
                    pictures_container = view['images']
                    break

            picture_urls = []

            for container in pictures_container:
                picture_url = 'https://miportal.entel.cl' + \
                              container['heroImage']
                picture_urls.append(picture_url.replace(' ', '%20'))

            product = Product(
                sku['skuName'],
                cls.__name__,
                'Cell',
                url,
                url,
                sku_id,
                stock,
                price,
                price,
                'CLP',
                sku=sku_id,
                cell_plan_name='Entel Prepago',
                picture_urls=picture_urls,
                description=description,
            )
            products.append(product)

        return products
