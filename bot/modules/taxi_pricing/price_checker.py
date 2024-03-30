import requests

class GeographicCoordinate:
    """
    Представление географических координат
    Широта (latitude), Долгота (longitude)
    """
    def __init__(self, latitude : float, longitude : float):
        # Широта
        self.latitude = latitude
        # Долгота
        self.longitude = longitude

class Route:
    """
    Описание маршрута: откуда(from_coords), куда(dest_coords).
    comment - Описание маршрута (пользовательский комментарий)
    """
    def __init__(self, from_coords : GeographicCoordinate, dest_coords : GeographicCoordinate, comment : str = ''):
        self.from_coords = from_coords
        self.dest_coords = dest_coords
        self.comment = comment

class TaxiRouteInfoApi:
    api_url = "https://taxi-routeinfo.taxi.yandex.net/taxi_info"
    headers = {
        "Accept": "application/json"
    }
    def __init__(self, CLID : str, APIKEY : str):
        self.params = {
            "rll": "",
            "clid": CLID,
            "apikey": APIKEY,
            "class" : ""
        }

    def request(self, route : Route, taxi_class : str = "econom,business,comfortplus") -> requests.Response:
        self.params["rll"] = f"{route.from_coords.longitude},{route.from_coords.latitude}~{route.dest_coords.longitude},{route.dest_coords.latitude}"
        self.params["class"] = f"{taxi_class}"

        return requests.get(url=TaxiRouteInfoApi.api_url, params=self.params, headers=TaxiRouteInfoApi.headers)

def seconds_to_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))

class RouteInfo:
    def __init__(self, distance : float, time : float, options : dict):
        self.distance : float = distance    # Длина маршрута, м
        self.travel_time : float = time     # Время поездки, сек
        self.options = options
        # self.class_name : str = options['class_name']
        # self.class_level : int = options['class_level']
        # self.price : float = options['price']
        # self.waiting_time : float = options.get('waiting_time', -1)

    def class_level(self) -> int:
        return self.options['class_level']

    def price(self) -> float:
        return self.options['price']

    def time(self) -> float:
        return seconds_to_time(self.travel_time)

    def waiting_time(self) -> float:
        return seconds_to_time(self.options['waiting_time']) if 'waiting_time' in self.options else "unknown"

    def __str__(self):
        return f'''
    Длина маршрута, м: {self.distance}
    Время поездки: {self.time()}
    Тариф поездки: {self.options['class_text']}
    Время ожидания машины: {self.waiting_time()}
    Стоимость поездки: {self.price()}
    '''

def parse_response(response : requests.Response) -> list[RouteInfo]:
    data = response.json()
    distance=data['distance']
    time=data['time']
    return [RouteInfo(distance=distance, time=time, options=options) for options in data['options']]
