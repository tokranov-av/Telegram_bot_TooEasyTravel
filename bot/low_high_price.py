import json
from datetime import date, timedelta
from typing import Dict

import requests

from bot.function import hotel_search


def hotel_search_sort(quantity: int, city_id: int, api_key: str, search_kind: str) -> Dict[str, float]:
    """
    Функция, выполняющая запрос по адресу,  указанному в переменной url и копирующая необходимую информацию об отелях
     из полученных данных в отдельный словарь.
    В запросе на сайт передается идентификатор города, где расположены отели и количество отелей. Сайт может передать
     информацию о 25 отелях максимум за один запрос. После выполнения запроса сайт передает JSON-файл c данными об
      отелях в интересующемся городе. Полученный JSON-файл конвертируется в словарь и передается в функцию
       hotel_search для извлечения из него необходимой информации: наименований отелей и стоимости снятия номера на
        ночь в соответствующем отеле.

    :param quantity:  количество отелей (int)
    :param city_id: идентификационный номер города (int)
    :param api_key: ключ доступа на хост (str)
    :param search_kind: вид сортировки, который будет осуществлен в полученных данных (str)
    :return: словарь с данными отелей. Каждый элемент словаря: ключ: наименование отеля, значение ключа: стоимость
     снятия номера на ночь в отеле (Dict).
    """
    current_quantity = quantity
    previous_quantity, retry_flag = 0, 0
    final_hotels = dict()
    date_today = str(date.today())
    date_tomorrow = str(date.today() + timedelta(days=1))
    url = 'https://hotels4.p.rapidapi.com/properties/list'

    for request_number in range(1, 11):  # Делаем не более 10 запросов
        print('Запрос на сайт:', request_number)
        querystring = {'adults1': '1', 'pageNumber': str(request_number), 'destinationId': str(city_id),
                       'pageSize': '25', 'checkOut': date_tomorrow, 'checkIn': date_today, 'sortOrder': search_kind,
                       'locale': 'ru_RU', 'currency': 'RUB'}
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'hotels4.p.rapidapi.com'
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        data = json.loads(response.text)
        final_hotels.update(hotel_search(data=data, quantity=current_quantity))

        current_length = len(final_hotels)
        current_quantity = quantity - current_length

        # Если количество отелей равно или выше запрошенного или флаг повтора равен двум, выходим из цикла
        if len(final_hotels) >= quantity or retry_flag == 2:
            break
        # Считаем количество повторов
        if previous_quantity == current_length and current_length > 0:
            retry_flag += 1
        else:
            retry_flag = 0

        previous_quantity = len(final_hotels)

    if len(final_hotels) > 1:
        final_hotels = {i_key: i_value for i_key, i_value in sorted(final_hotels.items(), key=lambda elem: elem[1][1])}

    return final_hotels
