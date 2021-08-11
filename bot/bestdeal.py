import json
from datetime import date, timedelta
from typing import Dict, List

import requests

from bot.function import hotel_search_distance


def hotel_search_range(quantity: int, city_id: int, minimum_price: int, maximum_price: int,
                       minimum_distance: float, maximum_distance: float, api_key: str) -> Dict[str, List[float]]:
    """
    Функция, выполняющая запрос по адресу, указанному в переменной url и копирующая необходимую информацию об отелях
     из полученных данных в отдельный словарь.
    В запросе на сайт передается идентификатор города, где расположены отели, диапазон цен и расстояний от центра
     города до предполагаемых отелей, а также количество отелей. Сайт может передать информацию о 25 отелях максимум.
    После выполнения запроса, сайт передает JSON-файл c данными об отелях в интересующемся городе. Полученный JSON-файл
     конвертируется в словарь и передается в функцию hotel_search_distance для извлечения из данного словаря
      интересующейся информации, а именно, наименований отелей, стоимости снятия номера на ночь в соответствующем
       отеле и расстояния от центра до конкретного отеля.
    Необходимо отметить, что данные, полученные с сайта уже приходят отсортированные по стоимости от минимального к
     максимальному. Для этого, до выполнения запроса на сайт, в переменной querystring ключу 'sortOrder' необходимо
      присвоить значение 'PRICE'.
    Функция hotel_search_distance возвращает словарь, после чего передается далее.

    :param quantity: количество отелей (int)
    :param city_id: идентификационный номер города (int)
    :param minimum_price: минимальная стоимость, необходимая для снятия номера на ночь в рублях (float)
    :param maximum_price: максимальная стоимость, необходимая для снятия номера на ночь в рублях (float)
    :param minimum_distance: минимальная дистанция от центра до отеля в километрах (float)
    :param maximum_distance: максимальная дистанция от центра до отеля в километрах (float)
    :param api_key: ключ доступа на хост
    :return: словарь с данными отелей. Каждый элемент словаря - ключ: наименование отеля, значение ключа: список, где
     элемент с индексом "0" - стоимость снятия номера на ночь, элемент с индексом "1" - дистанция от центра до данного
      отеля (Dict).
    """
    final_hotels = dict()
    date_today = str(date.today())
    date_tomorrow = str(date.today() + timedelta(days=1))
    previous_quantity, retry_flag = 0, 0

    url = 'https://hotels4.p.rapidapi.com/properties/list'
    current_quantity = quantity

    for request_number in range(1, 11):  # Делаем не более 10 запросов
        print('Запрос на сайт:', request_number)
        querystring = {'adults1': '1', 'pageNumber': str(request_number), 'destinationId': str(city_id),
                       'pageSize': '25', 'checkOut': date_tomorrow, 'checkIn': date_today,
                       'priceMax': str(maximum_price), 'sortOrder': 'PRICE', 'locale': 'ru_RU',
                       'currency': 'RUB', 'priceMin': str(minimum_price), 'landmarkIds': 'City center'}
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'hotels4.p.rapidapi.com'
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        data_site = json.loads(response.text)
        current_hotels = hotel_search_distance(data=data_site,
                                               quantity=current_quantity,
                                               distance_minimum=minimum_distance,
                                               distance_maximum=maximum_distance,
                                               price_min=minimum_price,
                                               price_max=maximum_price)
        final_hotels.update(current_hotels[0])
        current_length = len(final_hotels)
        current_quantity = quantity - current_length

        # Если количество отелей равно или выше запрошенного, цена выше запрошенного или флаг повтора равен двум,
        # выходим из цикла
        if len(final_hotels) >= quantity or current_hotels[1] > maximum_price or retry_flag == 2:
            break
        # Считаем количество повторов
        if previous_quantity == current_length and current_length > 0:
            retry_flag += 1
        else:
            retry_flag = 0

        previous_quantity = len(final_hotels)

    if len(final_hotels) > 1:  # Сортировка по цене
        final_hotels = {i_key: i_value for i_key, i_value in sorted(final_hotels.items(), key=lambda elem: elem[1][1])}

    return final_hotels
