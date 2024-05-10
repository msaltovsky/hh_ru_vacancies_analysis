import matplotlib.pyplot as plt
import pandas as pd


def visualize_avg_salary_in_moscow(given_datasets, mo_gdf):
    """
    Визуализация средней зарплат в вакансиях для отдельных административных райново Москвы.
    :param given_datasets: Датасеты вакансий, отдельный датасет отвечает за одну отрасль.
    :param mo_gdf: Таблица с записями административных районов и их границами.
    :return: ничего
    """
    for dataset in given_datasets:
        adm_districts_avg_salaries = {
        "ЦАО": 0,
        "ЮАО": 0,
        "ЮВАО": 0,
        "САО": 0,
        "ЗАО": 0,
        "СВАО": 0,
        "ВАО": 0,
        "Новомосковский": 0,
        "ЮЗАО": 0,
        "СЗАО": 0,
        "ЗелАО": 0,
        "Троицкий": 0,
        "Не в Москве": 0
        }
        for ao in adm_districts_avg_salaries.keys():
            adm_districts_avg_salaries[ao] = dataset.loc[dataset["AO"] == ao, "salary"].mean()
        df_to_salary = mo_gdf[["ABBREV_AO", "geometry"]]
        df_to_salary["avg_salary"] = pd.Series(df_to_salary["ABBREV_AO"].apply(lambda x: adm_districts_avg_salaries[x]))
        salaries = df_to_salary.to_crs(epsg='3857') #непосредственно преобразование проекции
        salaries.plot(column = 'avg_salary', linewidth=0.5, cmap='plasma', legend=True, figsize=[15,15])
        plt.title(dataset["industry"][0])
        plt.xticks([])
        plt.yticks([])
        plt.show()
