import math
import numpy as np
import pandas as pd
from shapely.geometry import Point


def get_net_salary(salary_cell):
    """
    Получить зарплату. Если зарплата имеет только нижний или только верхний порог, выберите ее как зарплату.
    Если присутствуют оба порога, рассчитайте среднее значение.
    Если тип зарплаты указан как брутто, то рассчитайте чистую зарплату после уплаты налогов (13%).
    :param salary_cell: Информация о зарплате.
    :return: Чистая зарплата.
    """
    value_from = salary_cell["from"]
    value_to = salary_cell["to"]
    if value_from is None or value_to is None:
        salary = value_from if value_from is not None else value_to
    else:
        salary = (value_from + value_to)/2
    if salary_cell["gross"]:
        salary *= 0.87
    return salary


def distance_in_meters(lat1, lon1, lat2, lon2):
    """
    Рассчитать расстояние между двумя точками в метрах.
    :param lat1: Широта первой точки.
    :param lon1: Долгота первой точки.
    :param lat2: Широта второй точки.
    :param lon2: Долгота второй точки.
    :return: Расстояние в метрах.
    """
    # радиус Земли на широте Москвы (55.7558° с.ш.) в метрах
    r_moscow = 6378137.0  # Approximate radius of the Earth at Moscow's latitude in meters

    # преобразование широты и долготы из градусов в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # разница в широте и долготе
    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad

    # формула Хаверсина
    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in meters
    distance = r_moscow * c

    return distance


def get_stations_count_and_distance_to_nearest(address, stations):
    """
    Подсчитывает количество ближайших станций метро и расстояние до ближайшей станции метро.
    :param stations: Станции в городе.
    :param address: Ячейка адреса в наборе данных, содержащая параметры адреса.
    :return: Количество ближайших станций метро и расстояние до ближайшей станции метро.
    """
    if address is None:
        return None, None
    num_stations = 0
    nearest = np.Inf
    lat_address, lon_address = address["lat"], address["lng"]
    if lat_address is not None and lon_address is not None:
        # Самая удаленная точка от Красной площади находится примерно в 79 км от нее,
        # так что за этим радиусом определенно не Москва.
        msc_lat, msc_lng = 55.751426, 37.618879
        if distance_in_meters(lat_address, lon_address, msc_lat, msc_lng) > 79000:
            return None, None
        for station in stations:
            dist_to_station = distance_in_meters(lat_address, lon_address, station[0], station[1])
            if dist_to_station < 1000:
                num_stations += 1
            nearest = min(nearest, dist_to_station)
    else:
        return None, None
    if nearest == np.Inf:
        return num_stations, None
    return num_stations, nearest


def within_a_polygon(lat, lon, polygon):
    """
    Проверяет, находится ли определенная точка внутри полигона.
    :param lat: Широта точки.
    :param lon: Долгота точки.
    :param polygon: Полигон
    :return: true, если точка находится внутри полигона, иначе false.
    """
    point = Point(lon, lat)
    return polygon.contains(point)


def find_AO(lat_lon, mo_gdf):
    """
    Находит административный округ по заданным широте и долготе.
    :param mo_gdf: Геофрейм данных, содержащий информацию о административных округах города.
    :param lat_lon: Серия с широтой и долготой.
    :return: Административный округ точки.
    """
    lat, lon = lat_lon.loc["lat"], lat_lon.loc["lon"]
    for idx in mo_gdf.index:
        if within_a_polygon(lat, lon, mo_gdf.loc[idx, "geometry"]):
            return mo_gdf.loc[idx, "ABBREV_AO"]
    return "Не в Москве"