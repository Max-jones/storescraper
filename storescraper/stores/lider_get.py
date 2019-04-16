import json
import urllib
from collections import OrderedDict

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, session_with_proxy, \
    check_ean13
from storescraper import banner_sections as bs


class LiderGet(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'VideoGameConsole',
            'AllInOne',
            'Projector',
            'SpaceHeater',
            'AirConditioner',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'Wearable',
            'Stove',
            'WaterHeater',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['Televisores', 'Television'],
            ['DVDs_y_Blu-Ray', 'OpticalDiskPlayer'],
            ['Audífonos', 'Headphones'],
            ['Audio_portable', 'StereoSystem'],
            ['Equipos_de_música', 'StereoSystem'],
            ['Consolas', 'VideoGameConsole'],
            ['Smartphones', 'Cell'],
            ['Celulares_básicos', 'Cell'],
            ['Smartwatch', 'Wearable'],
            ['Tarjetas_de_memoria', 'MemoryCard'],
            ['Notebooks', 'Notebook'],
            ['Convertibles', 'Notebook'],
            ['Gamers', 'Notebook'],
            ['All_in_One', 'AllInOne'],
            ['Tablets', 'Tablet'],
            ['Discos_duros', 'ExternalStorageDrive'],
            ['Pendrives', 'UsbFlashDrive'],
            ['Impresoras_y_Multifuncionales', 'Printer'],
            ['Teclados_y_Mouse', 'Mouse'],
            ['Accesorios_Gamers', 'Mouse'],
            ['Lavadoras_superiores', 'WashingMachine'],
            ['Lavadoras_frontales', 'WashingMachine'],
            ['Lavadoras_-_secadoras', 'WashingMachine'],
            ['Secadoras', 'WashingMachine'],
            ['Refrigeración', 'Refrigerator'],
            ['Enfriadores', 'AirConditioner'],
            ['Aire_acondicionado', 'AirConditioner'],
            ['Encimeras', 'Stove'],
            ['Cocina', 'Stove'],
            ['Horno_Empotrable', 'Oven'],
            ['Hornos_eléctricos', 'Oven'],
            ['Microondas', 'Oven'],
            ['Calefont', 'WaterHeater'],
            ['Estufas_eléctricas', 'SpaceHeater'],
            ['Aspiradoras__y_Limpieza', 'VacuumCleaner'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            query_url = 'https://529cv9h7mw-dsn.algolia.net/1/indexes/*/' \
                        'queries?x-algolia-application-id=529CV9H7MW&x-' \
                        'algolia-api-key=c6ab9bc3e19c260e6bad42abe143d5f4'

            query_params = {
                "requests": [
                    {
                        "indexName": "campaigns_production_price_desc",
                        "params": "hitsPerPage=1000&facetFilters=%5B%22"
                                  "categorias%3A{}%22%5D".format(
                                    urllib.parse.quote(
                                        category_id.replace('_', ' ')))
                    }
                ]
            }

            response = session.post(query_url, json.dumps(query_params))
            data = json.loads(response.text)

            if not data['results'][0]['hits']:
                raise Exception('Empty category: ' + category_id)

            for entry in data['results'][0]['hits']:
                product_urls.append('https://get.lider.cl/product/sku/'
                                    '{}'.format(entry['sku']))

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        sku_id = url.split('/')[-1]

        query_url = 'https://api.lider.cl/black-cyber/products/?sku={}' \
                    '&appId=BuySmart&ts=15554157446068'.format(sku_id)
        entry = json.loads(session.get(query_url).text)[0]

        name = '{} {}'.format(entry['brand'], entry['displayName'])
        ean = entry['gtin13']

        if not check_ean13(ean):
            ean = None

        sku = str(entry['sku'])
        stock = -1 if entry['available'] else 0
        normal_price = Decimal(entry['price']['BasePriceSales'])
        offer_price_container = entry['price']['BasePriceTLMC']

        if offer_price_container:
            offer_price = Decimal(offer_price_container)
        else:
            offer_price = normal_price

        specs = OrderedDict()
        for spec in entry['filters']:
            specs.update(spec)

        part_number = specs.get('Modelo')
        if part_number:
            part_number = part_number[:49]

        description = html_to_markdown(entry['longDescription'])

        picture_urls = ['https://images.lider.cl/wmtcl?source=url'
                        '[file:/productos/901210{}]&sink'.format(img)
                        for img in entry['imagesAvailables']]

        return [Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            ean=ean,
            part_number=part_number,
            picture_urls=picture_urls,
            description=description
        )]

    @classmethod
    def banners(cls, extra_args=None):
        base_url = 'https://www.lider.cl/electrohogar/{}'

        sections_data = [
            [bs.HOME, 'Home', bs.SUBSECTION_TYPE_HOME, ''],
            [bs.AUDIO, 'Audio Portable', bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrónica/Equipos-de-Audio/Audio-Portable/'
             '_/N-qfhc1c'],
            [bs.AUDIO, 'Equipos de Música', bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrónica/Equipos-de-Audio/Equipos-de-Música/'
             '_/N-ss8ejy'],
            [bs.CELLS, 'Smartphones', bs.SUBSECTION_TYPE_MOSAIC,
             'category/Telefonía-y-Fotografía/'
             'Celulares-y-Teléfonos/Smartphones/_/N-1orftrb'],
            [bs.REFRIGERATION, 'Refrigeradores No Frost',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrohogar/Refrigeración/Refrigeradores-No-Frost/'
             '_/N-7wqjz8'],
            [bs.REFRIGERATION, 'Refrigeradores Side By Side',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrohogar/Refrigeración/Refrigeradores-Side-By-Side/'
             '_/N-ihia7d'],
            [bs.WASHING_MACHINES, 'Lavadoras Superiores',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrohogar/Lavado-y-Secado/Lavadoras-Superiores/'
             '_/N-g2rcn0'],
            [bs.WASHING_MACHINES, 'Lavadoras - Secadoras',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrohogar/Lavado-y-Secado/Lavadoras-Secadoras/'
             '_/N-1xvutty'],
            [bs.TELEVISIONS, 'Televisores',
             bs.SUBSECTION_TYPE_MOSAIC,
             'category/Electrónica/Tv-y-Video/Televisores/_/N-j78dbl']
        ]

        session = session_with_proxy(extra_args)
        banners = []

        for section, subsection, subsection_type, url_suffix in sections_data:
            url = base_url.format(url_suffix)
            print(url)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            if subsection_type == bs.SUBSECTION_TYPE_HOME:
                images = soup.find('div', 'owl-carousel') \
                    .findAll('div', 'item', recursive=False)

                for index, image in enumerate(images):
                    picture_url = image.find('source')['srcset']
                    destination_link = image.find('a')

                    if destination_link:
                        destination_urls = [destination_link['href']]
                    else:
                        destination_urls = []

                    banners.append({
                        'url': url,
                        'picture_url': picture_url,
                        'destination_urls': destination_urls,
                        'key': picture_url,
                        'position': index + 1,
                        'section': section,
                        'subsection': subsection,
                        'type': subsection_type
                    })

            if subsection_type == bs.SUBSECTION_TYPE_MOSAIC:
                image = soup.find('div', 'template-listado').find('p')
                picture = image.find('img')
                if not picture:
                    continue
                picture_url = picture['src']
                destination_urls = [a['href'] for a in image.findAll('a')]
                banners.append({
                    'url': url,
                    'picture_url': picture_url,
                    'destination_urls': destination_urls,
                    'key': picture_url,
                    'position': 1,
                    'section': section,
                    'subsection': subsection,
                    'type': subsection_type
                })

        return banners
