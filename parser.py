# import libraries
import requests
import json
import datetime
import os
import pathlib
import tqdm
import numpy as np
import time
from requests import HTTPError


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
    industries = []
    retry_count = 5
    retry_delay = 1  # задержка между повторными запросами

    for _ in range(retry_count):
        try:
            industries_response = requests.get(url_industry, params=params, headers=headers)
            industries_response.raise_for_status()
            industries_response = industries_response.json()
            industries = [(element["id"], element["name"]) for element in industries_response]
            break  # если удачно, то выходим из цикла
        except requests.exceptions.HTTPError as err:
            if err.response.status_code in [400, 403]:
                print(f"Retrying due to HTTP error: {err}")
                time.sleep(retry_delay)
            else:
                print(err)
                break  # выходим из цикла, если ошибка не может быть обработана

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
            'currency': "RUR",
            "host": "hh.ru"
        }
        header_for_industry = {
            'HH-User-Agent': 'my-app/0.0.1'
        }
        for _ in range(retry_count):
            try:
                response_industry = requests.get(url_vacancies, params=params_for_industry, headers=header_for_industry)
                response_industry.raise_for_status()
                response_industry = response_industry.json()
                if len(top_tier_industries) < k:
                    top_tier_industries.append((response_industry["found"], industry_id, name))
                else:
                    found = [i[0] for i in top_tier_industries]
                    idx_min = np.argmin(found)
                    if top_tier_industries[idx_min][0] < response_industry["found"]:
                        top_tier_industries[idx_min] = (response_industry["found"], industry_id, name)
                time.sleep(np.random.uniform(0.005, 0.01))
                break  # если удачно, то выходим из цикла
            except requests.exceptions.HTTPError as err:
                if err.response.status_code in [400, 403]:
                    print(f"Retrying due to HTTP error: {err}")
                    time.sleep(retry_delay)
                else:
                    print(err)
                    break  # выходим из цикла, если ошибка не может быть обработана
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
    headers = {
        'HH-User-Agent': 'my-app/0.0.1',
    }
    url = 'https://api.hh.ru/vacancies'
    vacancies = None
    start_date = from_date
    extracted_all = False
    for i in range(number_of_vacancies // 100):
        params = {
            'area': area_id,
            'per_page': 100,
            'page': i,
            'date_from': start_date.strftime('%Y-%m-%d'),
            'date_to': until_date.strftime('%Y-%m-%d'),
            'industry': industry_id,
            'only_with_salary': True,
            'currency': "RUR",
            "host": "hh.ru"
        }
        retry_count = 5
        retry_delay = 1  # задержка между повторными попытками

        for _ in range(retry_count):
            try:
                response = requests.get(url, headers=headers, params=params)
                time.sleep(np.random.uniform(0.5, 2))
                response.raise_for_status()
                if vacancies is None:
                    vacancies = response.json()["items"]
                else:
                    vacancies.extend(response.json()['items'])

                if response.json()["found"] == 0 or i >= response.json()["pages"] - 1:
                    extracted_all = True
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [400, 403]:
                    print(f"Retrying due to HTTP error: {e}")
                    time.sleep(retry_delay)
                else:
                    print(e)
                    break  # выходим из цикла, если ошибка не может быть обработана
            except requests.exceptions.ConnectTimeout as e:
                time.sleep(2)
                print(f"Retrying due to connect timeout: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"Retrying due to connection error: {e}")
                time.sleep(20)
        if extracted_all:
            break
    # удаление ненужных признаков
    if not vacancies:
        return []
    return vacancies


def get_vacancies_by_parts(area_id, industry_id, from_date, until_date, number_of_parts):
    """
    Для более хорошего сбора данных используется деление всего временного промежутка на number_of_parts частей.
    :param area_id: Регион, в котором искать.
    :param industry_id: Отрасль вакансий.
    :param from_date: Начиная с даты.
    :param until_date: Заканчивая датой.
    :param number_of_parts: На какое кол-во частей делится временной интервал.
    :return: Все вакансии с изначального временного промежутка.
    """
    days_in_part = (until_date - from_date).days // number_of_parts
    from_date_part = from_date
    until_date_part = from_date_part + datetime.timedelta(days=days_in_part)
    vacancies = []

    def get_vacancies_part(start_date, end_date):
        try:
            return get_vacancies(area_id, 2000, industry_id, start_date, end_date)
        except ConnectionError as e:
            print(f"ConnectionError occurred: {e}")
            # ожидание 5 минут для повторного запроса
            time.sleep(300)
            return get_vacancies(area_id, 2000, industry_id, start_date, end_date)

    for i in tqdm.tqdm(range(number_of_parts)):
        if i == number_of_parts - 1:
            until_date_part = until_date
        vacancies.extend(get_vacancies_part(from_date_part, until_date_part))
        from_date_part = until_date_part
        until_date_part = from_date_part + datetime.timedelta(days=days_in_part)
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


def clear_data(vacancies):
    """
    Очищает данные о вакансиях от лишней информации и обновляет их сведения о работодателе и контактах.

    :param vacancies: Список словарей, представляющих данные о вакансиях.
    :return: Список словарей с обновленными данными о вакансиях.
    """
    headers = {
        'HH-User-Agent': 'my-app/0.0.1',
    }

    def process_vacancy(vac, retry_count):
        """
        Обрабатывает отдельную вакансию, удаляя лишнюю информацию и обновляя данные о работодателе и контактах.

        :param vac: Словарь с данными о вакансии.
        :param retry_count: Количество попыток для повторной загрузки данных о работодателе.
        :return: Обновленные данные о вакансии.
        """
        # Определение ключей, которые нужно оставить
        needed_keys = ["is_adv_vacancy", "employment", "experience", "accept_incomplete_resumes", "accept_temporary",
                       "working_time_modes", "working_time_intervals", "working_days", "schedule", "employer",
                       "address", "salary", "response_letter_required", "has_test", "department", "premium",
                       "professional_roles", "contacts", "type", "archived"]
        # Удаление лишних ключей из вакансии
        keys_to_remove = set(vac.keys()).difference(set(needed_keys))
        for key in keys_to_remove:
            vac.pop(key)

        # Получение значения для нового ключа "employer_trusted"
        vac["employer_trusted"] = vac["employer"]["trusted"]

        # Получение идентификатора работодателя
        emp_id = vac["employer"].get("id")

        # Получение данных о работодателе через API HeadHunter
        if emp_id is not None:
            response = None
            for _ in range(retry_count):
                try:
                    response = requests.get(f'https://api.hh.ru/employers/{emp_id}', headers=headers)
                    time.sleep(np.random.uniform(0.5, 2))
                    response.raise_for_status()
                    response = response.json()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code in [400, 403]:
                        print(f"Retrying due to HTTP error: {e}")
                    else:
                        break
                except requests.exceptions.ConnectTimeout as e:
                    time.sleep(2)
                    print(f"Retrying due to connect timeout: {e}")
                except requests.exceptions.ConnectionError as e:
                    print(f"Retrying due to connection error: {e}")
                    time.sleep(20)
            else:
                response = None
            if response is not None:
                # Обновление данных вакансии на основе данных о работодателе
                vac["employer_type"] = response.get("type", "Скрыт")
                vac["industries_count"] = max(1, len(response.get("industries", [])))
                vac["vacancies_count"] = response.get("open_vacancies", 1)
            else:
                vac["employer_type"] = None
                vac["industries_count"] = 1
                vac["vacancies_count"] = 1

        # Удаление ключа "employer" из вакансии
        vac.pop("employer")

        # Обработка контактной информации
        if vac["contacts"] is not None:
            vac["has_email"] = bool(vac["contacts"].get("email"))
            vac["phones_count"] = len(vac["contacts"].get("phones", []))
        else:
            vac["has_email"] = False
            vac["phones_count"] = 0
        vac.pop("contacts")

        # Обновление ключей "vacancy_type", "lat" и "lon"
        vac["vacancy_type"] = vac["type"]["name"]
        vac.pop("type")
        if vac["address"] is not None:
            vac["lat"] = vac["address"]["lat"]
            vac["lon"] = vac["address"]["lng"]
        else:
            vac["lat"] = None
            vac["lon"] = None
        vac.pop("address")
        vac["schedule"] = vac["schedule"]["name"] if vac["schedule"] is not None else None
        vac["experience"] = vac["experience"]["name"] if vac["experience"] is not None else None
        vac["employment"] = vac["employment"]["name"] if vac["employment"] is not None else None
        return vac

    def process_vacancies(vacancies, retry_count):
        """
        Обрабатывает вакансии параллельно, используя tqdm для отображения прогресса.

        :param vacancies: Список словарей с данными о вакансиях.
        :param retry_count: Количество попыток для повторной загрузки данных о работодателе.
        :return: Список словарей с обновленными данными о вакансиях.
        """
        bar = tqdm.tqdm(total=len(vacancies))
        bar.set_description(f"Очищение {len(vacancies)} вакансий")
        processed_vacancies = []
        for vac in vacancies:
            processed_vacancies.append(process_vacancy(vac, retry_count))
            bar.update(1)
        return processed_vacancies

    # Вызов функции parallel_process_vacancies с параметром retry_count равным 5
    return process_vacancies(vacancies, 5)


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
    search_from_date = datetime.datetime(2024, 4, 1)
    search_until_date = datetime.datetime(2024, 5, 26)
    moscow_city_id = 1
    print("Выбираем топ индустрии по количеству вакансий")
    k = 3
    top_industries = get_top_k_industries(k, moscow_city_id, search_from_date, search_until_date)
    print("\nВыбрано!")

    for i, ind in enumerate(top_industries):
        with open(f"datasets/industry({ind[2]}).json", "w", encoding='utf-8') as outfile:

            print(f"\nСобираем вакансии{i+1}/{k}")
            cleared_vacancies = clear_data(
                get_vacancies_by_parts(moscow_city_id, ind[1], search_from_date, search_until_date,
                                       (search_until_date - search_from_date).days))
            json.dump(cleared_vacancies,
                      outfile, ensure_ascii=False, indent=4)
    # сохранить координаты (широту и долготу) для каждой станции метро в Москве
    if not os.path.exists("src_files/stations.npy"):
        np.save("src_files/stations.npy", get_metro_stations_in_city(moscow_city_id))
