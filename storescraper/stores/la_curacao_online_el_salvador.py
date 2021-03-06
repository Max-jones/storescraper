from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineElSalvador(LaCuracaoOnline):
    country = 'elsalvador'
    currency = '$'
    currency_iso = 'USD'
    category_filters = [
        ('telefonia/celulares', 'Cell'),
        ('audio-y-video/televisores.html', 'Television'),
        ('audio-y-video/equipos-de-sonido.html', 'StereoSystem'),
        # ('audio-y-video/reproductores-de-video.html', 'OpticalDiskPlayer'),
        ('aires-acondicionados', 'AirConditioner'),
        ('refrigeracion/refrigeradoras.html', 'Refrigerator'),
        ('refrigeracion/congeladores.html', 'Refrigerator'),
        ('lavadoras-y-secadoras/lavadoras.html', 'WashingMachine'),
        ('lavadoras-y-secadoras/secadoras.html', 'WashingMachine'),
        ('cocina/microondas.html', 'Oven'),
        ('cocina/cocinas-de-gas.html', 'Stove'),
    ]
