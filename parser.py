# import libraries
import requests
import json
import time
import datetime
import numpy as np
import os
import pathlib
import tqdm


def get_top_k_industries(k, area_id, since_date, until_date):
    """
    Возвращает топ-K отраслей по количеству найденных вакансий.
    :param k: Количество отраслей для возврата.
    :param area_id: Идентификатор района https://github.com/hhru/api/blob/master/docs/areas.md
    :param since_date: Дата, с которой начать поиск отраслей.
    :param until_date: Дата, до которой вести поиск отраслей.
    :return: Массив из топ-K отраслей в формате [(количество_вакансий, идентификатор_отрасли, название_отрасли)]
    """
    url_industry = 'https://api.hh.ru/industries'
    url_vacancies = 'https://api.hh.ru/vacancies'
    params = {
    }
    headers = {
        'HH-User-Agent': 'my-app/0.0.1'
    }
    # получение всех отраслей
    industries_response = requests.get(url_industry, params=params, headers=headers)
    industries_response.raise_for_status()
    industries_response = industries_response.json()
    industries = [(element["id"], element["name"]) for element in industries_response]
    start_date = since_date
    top_tier_industries = []
    # выбор топ K отраслей по количеству найденных вакансий
    bar = tqdm.tqdm(industries)
    for industry_id, name in bar:
        params_for_industry = {
            'industry_id': industry_id,
            'date_from': start_date.strftime('%Y-%m-%d'),
            'date_to': until_date.strftime('%Y-%m-%d'),
            'area': area_id,
            'only_with_salary': True,
            'currency': "RUR"
        }
        header_for_industry = {
            'HH-User-Agent': 'my-app/0.0.1'
        }
        response_industry = requests.get(url_vacancies, params=params_for_industry, headers=header_for_industry)
        response_industry.raise_for_status()
        if response_industry.status_code == 200:

            response_industry = response_industry.json()
            if len(top_tier_industries) < k:
                top_tier_industries.append((response_industry["found"], industry_id, name))
            else:
                found = [i[0] for i in top_tier_industries]
                idx_min = np.argmin(found)
                if top_tier_industries[idx_min][0] < response_industry["found"]:
                    top_tier_industries[idx_min] = (response_industry["found"], industry_id, name)
        time.sleep(np.random.uniform(0.5, 2.0))
    return top_tier_industries


def get_vacancies(area_id, number_of_vacancies, industry_id, from_date, until_date):
    """
    Получить вакансии по городу и количество вакансий в определенной отрасли.
    :param area_id: Идентификатор конкретного района для поиска вакансий,
    который можно найти по ссылке https://github.com/hhru/api/blob/master/docs/areas.md.
    :param number_of_vacancies: Количество вакансий для возврата.
    :param industry_id: Конкретная отрасль,
    https://api.hh.ru/openapi/redoc#tag/Obshie-spravochniki/operation/get-industries.
    :param from_date: Начальная дата для поиска вакансий.
    :param until_date: Дата, до которой вести поиск вакансий.
    :return: Найденные вакансии по заданным ограничениям.
    """
    url = 'https://api.hh.ru/vacancies'
    headers = {
        'HH-User-Agent': 'my-app/0.0.1'
    }
    vacancies = None
    start_date = from_date
    for i in range(number_of_vacancies // 100):
        params = {
            'area': area_id,
            'per_page': 100,
            'page': i,
            'date_from': start_date.strftime('%Y-%m-%d'),
            'date_to': until_date.strftime('%Y-%m-%d'),
            'industry': industry_id,
            'only_with_salary': True,
            'currency': "RUR"
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        if vacancies is None:
            vacancies = response.json()
        else:
            vacancies['items'].extend(response.json()['items'])
        if response.json()["page"] == response.json()["pages"]-1:
            break
        time.sleep(np.random.uniform(0.5, 2.0))

    for vac in vacancies['items']:
        for key in ("area", "type", "response_url", "sort_point_distance", "published_at", "created_at", "archived",
                    "apply_alternate_url", "brand_snippet",
                    "branding", "show_logo_in_search", "insider_interview", "url", "alternate_url", "relations",
                    "contacts", "adv_context", "adv_response_url", "immediate_redirect_url"):
            if key in vac.keys():
                vac.pop(key)
        vac["employer"] = {"trusted": vac["employer"]["trusted"]}
    return vacancies["items"]


def get_vacancies_by_parts(area_id, industry_id, from_date, until_date, number_of_parts):
    days_in_part = (until_date - from_date).days // number_of_parts
    from_date_part = from_date
    until_date_part = from_date_part + datetime.timedelta(days=days_in_part-1)
    vacancies = None
    bar = tqdm.tqdm(range(number_of_parts))
    for i in bar:
        if i == number_of_parts - 1:
            until_date_part = until_date
        if vacancies is None:
            vacancies = get_vacancies(area_id, 2000, industry_id, from_date_part, until_date_part)
        else:
            vacancies.extend(get_vacancies(area_id, 2000, industry_id, from_date_part, until_date_part))
        from_date_part = until_date_part + datetime.timedelta(days=1)
        until_date_part = from_date_part + datetime.timedelta(days=days_in_part-1)
    return vacancies


def get_metro_stations_in_city(city_id):
    """
    Получить координаты станций метро в определенном городе.
    :param city_id: Идентификатор конкретного города.
    :return: Координаты станций метро в городе, указанном по city_id.
    """
    url_stations = f'https://api.hh.ru/metro/{city_id}'
    params = {
    }
    headers = {
        'HH-User-Agent': 'my-app/0.0.1'
    }
    stations_response = requests.get(url_stations, params=params, headers=headers)
    stations_response.raise_for_status()
    stations_response = stations_response.json()
    np_stations = np.empty((0, 2))
    for line in stations_response["lines"]:
        for station in line["stations"]:
            np_stations = np.append(np_stations, np.array([station["lat"], station["lng"]], ndmin=2), axis=0)
    return np_stations


def clear_directory(directory):
    """
    Очистка указанной директории.
    :param directory: Директория для очистки.
    :return: Ничего
    """
    # существует ли директория
    if os.path.exists(directory):
        # все файлы внутри директории
        for file_name in os.listdir(directory):
            # полный путь до файла
            full_path = os.path.join(directory, file_name)
            # проверка на файл
            if os.path.isfile(full_path):
                # удаление файла
                os.remove(full_path)
            # если директория рекурсивно запускается удаление
            elif os.path.isdir(full_path):
                clear_directory(full_path)
        # удаление самой директории
        os.rmdir(directory)
        print(f"Directory '{directory}' cleared successfully.")
    else:
        print(f"Directory '{directory}' does not exist.")


if __name__ == '__main__':
    # очистить каталог datasets, если он существует, а затем создать его заново
    directory_path = "datasets"
    clear_directory(directory_path)
    pathlib.Path('datasets').mkdir(parents=True, exist_ok=True)
    # сохранить вакансии для каждой отрасли в top_industries по количеству найденных вакансий
    search_from_date = datetime.datetime(2024, 3, 1)
    search_until_date = datetime.datetime(2024, 5, 10)
    moscow_city_id = 1
    print("Выбираем топ индустрии по количеству вакансий")
    k = 3
    top_industries = get_top_k_industries(k, moscow_city_id, search_from_date, search_until_date)
    print("\nВыбрано!")
    for i, ind in enumerate(top_industries):
        print(ind)
        with open(f"datasets/industry({ind[2]}).json", "w", encoding='utf-8') as outfile:
            print(f"\nСобираем вакансии{i+1}/{k}")
            json.dump(get_vacancies_by_parts(moscow_city_id, ind[1], search_from_date, search_until_date, 15),
                      outfile, ensure_ascii=False, indent=4)
    # сохранить координаты (широту и долготу) для каждой станции метро в Москве
    if not os.path.exists("src_files/stations.npy"):
        np.save("src_files/stations.npy", get_metro_stations_in_city(moscow_city_id))
