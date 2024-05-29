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


def plot_yreal_ypred(y_test, y_train, y_test_hat, y_train_hat):
    """
        Рисует картинку для прогнозов регрессии. Взят из андана 3 домашняя.
    """

    margin = 0.1  # отступ на границах
    plt.figure(figsize=(10, 5))
    plt.subplot(121)
    plt.scatter(y_train, y_train_hat, color="red", alpha=0.5)
    plt.xlabel('Истинные значения')
    plt.ylabel('Предсказанные значения')
    plt.axis('equal')
    plt.axis('square')
    train_min = min(y_train)
    train_max = max(y_train)
    plt.xlim(train_min - margin, train_max + margin)
    plt.ylim(train_min - margin, train_max + margin)
    plt.plot([train_min - margin, train_max + margin], [train_min - margin, train_max + margin])
    plt.title('Train set', fontsize=20)

    plt.subplot(122)
    plt.scatter(y_test, y_test_hat, color="red", alpha=0.5)
    plt.xlabel('Истинные значения')
    plt.ylabel('Предсказанные значения')
    plt.axis('equal')
    plt.axis('square')
    test_min = min(y_test)
    test_max = max(y_test)

    plt.xlim(test_min - margin, test_max + margin)
    plt.ylim(test_min - margin, test_max + margin)
    plt.plot([test_min - margin, test_max + margin], [test_min - margin, test_max + margin])
    plt.title('Test set', fontsize=20)
    pass
