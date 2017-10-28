import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Kabum(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['hardware/ssd-2-5', 'SolidStateDrive'],
            ['hardware/disco-rigido-hd/externo-firewire',
             'ExternalStorageDrive'],
            ['hardware/disco-rigido-hd/externo-usb', 'ExternalStorageDrive'],
            ['hardware/disco-rigido-hd/portatil-usb', 'ExternalStorageDrive'],
            ['perifericos/pen-drive', 'UsbFlashDrive'],
            ['hardware/disco-rigido-hd/sata-3-5', 'StorageDrive'],
            ['hardware/disco-rigido-hd/sata-2-5-notebook', 'StorageDrive'],
            ['cameras-digitais/cartoes-de-memoria', 'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                category_url = 'http://www.kabum.com.br/{}?limite=100&' \
                               'pagina={}'.format(category_path, page)
                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(category_url).content,
                                     'html.parser')

                containers = soup.findAll('div', 'listagem-box')

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for container in containers:
                    product_id = container.find('a')['data-id']
                    product_url = 'https://www.kabum.com.br/cgi-local/site/' \
                                  'produtos/descricao_ofertas.cgi?codigo=' + \
                                  product_id
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).content.decode('latin-1')

        pricing_data = json.loads(re.search(
            r'dataLayer = ([\S\s]+?);\s', page_source).groups()[0])[0][
            'productsDetail'][0]

        name = pricing_data['name'].strip()
        sku = pricing_data['id'].strip()

        if pricing_data['available']:
            stock = -1
        else:
            stock = 0

        offer_price = Decimal(pricing_data['price'])

        soup = BeautifulSoup(page_source, 'html.parser')

        normal_price_container = soup.find('div', 'preco_desconto-cm')

        if normal_price_container:
            normal_price = Decimal(
                normal_price_container.text.replace(
                    'R$', '').replace('.', '').replace(',', '.'))
        else:
            normal_price = Decimal(
                soup.find('div', 'preco_normal').text.replace(
                    'R$', '').replace('.', '').replace(',', '.'))

        description = html_to_markdown(str(soup.find('div', 'content_tab')))

        picture_urls = [tag['src'] for tag in
                        soup.find('ul', {'id': 'imagem-slide'}).findAll('img')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'BRL',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]
