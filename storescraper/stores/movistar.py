import json

import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Movistar(Store):
    prepago_url = 'http://ww2.movistar.cl/prepago/'
    planes_url = 'https://planes.movistar.cl/'
    portability_choices = [
        (3, ''),
        (1, ' Portabilidad'),
    ]
    movistar1 = 0

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'CellPlan':
            product_urls.extend([
                cls.prepago_url,
                cls.planes_url
            ])
        elif category == 'Cell':
            catalogo_url = 'https://catalogo.movistar.cl/equipomasplan/' \
                           'catalogo.html?limit=1000'
            session = session_with_proxy(extra_args)
            soup = BeautifulSoup(session.get(catalogo_url).text, 'html.parser')
            containers = soup.findAll('li', 'product')

            if not containers:
                raise Exception('No cells found')

            for container in containers:
                product_urls.append(container['data-producturl'])

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'Movistar Prepago',
                cls.__name__,
                category,
                url,
                url,
                'Movistar Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif 'catalogo.movistar.cl' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url, timeout=30).text, 'html5lib')
        products = []

        plan_containers = soup.find('section', 'listadoplanes-box').findAll(
            'div', 'item')

        for plan_container in plan_containers:
            plan_link = plan_container.find('a')
            plan_url = plan_link['href']

            base_plan_name = 'Plan ' + plan_link.text.strip()
            base_plan_name = base_plan_name.replace('&nbsp;', '')

            price_text = plan_container.find('span', 'monto').text
            price = Decimal(remove_words(price_text.split('\xa0')[1]))

            portability_suffixes = ['', ' Portabilidad']
            cuotas_suffixes = [
                ' (sin cuota de arriendo)',
                ' (con cuota de arriendo)'
            ]

            for portability_suffix in portability_suffixes:
                for cuota_suffix in cuotas_suffixes:
                    plan_name = '{}{}{}'.format(
                        base_plan_name, portability_suffix, cuota_suffix)

                    products.append(Product(
                        plan_name,
                        cls.__name__,
                        'CellPlan',
                        plan_url,
                        url,
                        plan_name,
                        -1,
                        price,
                        price,
                        'CLP'
                    ))

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        base_name = soup.find('h1').text.strip()

        sku_color_choices = []
        for color_container in soup.find('div', 'color-select').findAll('li'):
            color_element = color_container.find('span')
            sku = color_element['data-sku']
            color_id = color_element['data-id']
            color_name = color_element['data-nombre-color']
            sku_color_choices.append((sku, color_id, color_name))

        plan_ids = []
        plan_containers = soup.find(
            'ul', 'modal-select-ul-planes').findAll('li')
        for plan_container in plan_containers:
            plan_ids.append(plan_container['data-id'])

        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        session.headers['x-requested-with'] = 'XMLHttpRequest'
        products = []

        for sku, color_id, color_name in sku_color_choices:
            name = '{} {}'.format(base_name, color_name)

            for plan_id in plan_ids:
                for portability_type_id, portability_suffix in \
                        cls.portability_choices:
                    payload = 'current%5Bsku%5D={}&current%5Bplan%5D={}&' \
                              'current%5Bmovistar1%5D={}&current%5Bpayment' \
                              '%5D=1&current%5Bcolor%5D={}&current%5Btype' \
                              '%5D={}'.format(sku, plan_id.replace(' ', '+'),
                                              cls.movistar1,
                                              color_id, portability_type_id)

                    response = session.post(
                        'https://catalogo.movistar.cl/equipomasplan/'
                        'emp_detalle/offer',
                        data=payload)

                    if response.status_code == 500:
                        continue

                    json_response = json.loads(response.text)
                    products.extend(cls._assemble_postpago_cells(
                        json_response, name, url, sku, color_id, plan_id,
                        portability_suffix))

        return products

    @classmethod
    def _assemble_postpago_cells(cls, json_response, name, url, sku, color_id,
                                 plan_id, portability_suffix):
        soup = BeautifulSoup(json_response['offer'], 'html.parser')
        payment_options = soup.findAll('div', 'price')

        products = []

        # Sin cuota de arriendo
        price = Decimal(remove_words(
            payment_options[0].contents[2]))

        products.append(Product(
            name,
            cls.__name__,
            'Cell',
            url,
            url,
            '{} - {} - {}{}'.format(sku, color_id, plan_id,
                                    portability_suffix),
            -1,
            price,
            price,
            'CLP',
            cell_plan_name='{}{}'.format(plan_id,
                                         portability_suffix),
            cell_monthly_payment=Decimal(0)
        ))

        # Con cuota de arriendo
        price = Decimal(remove_words(
            payment_options[1].contents[2]))
        monthly_payment_text = \
            soup.findAll('div', 'cuotes')[1].text
        monthly_payment_match = re.search(
            r'\$([\d|.]+)', monthly_payment_text)
        monthly_payment = Decimal(
            remove_words(monthly_payment_match.groups()[0]))

        products.append(Product(
            name,
            cls.__name__,
            'Cell',
            url,
            url,
            '{} - {} - {}{} cuotas'.format(sku, color_id, plan_id,
                                           portability_suffix),
            -1,
            price,
            price,
            'CLP',
            sku=sku,
            cell_plan_name='{}{} cuotas'.format(
                plan_id, portability_suffix),
            cell_monthly_payment=monthly_payment
        ))

        return products
