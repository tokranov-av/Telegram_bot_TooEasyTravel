import re
import json
import requests
from typing import Dict


def city_search(city: str, api_key: str, local: str) -> Dict[str, str]:
    """
    Функция, выполняющая запрос по адресу, указанному в переменной url и копирующая название города и его
     идентификационный номер из полученных данных в отдельный словарь.
    В запросе на сайт передается название города.
    После выполнения запроса, сайт передает JSON-файл, где приведены разные объекты со введенным названием.
     Полученный JSON-файл конвертируется в словарь, после чего из данного словаря извлекаются названия городов при
      выполнении условия: наименование переданного пользователем города должно соответствовать наименованию в словаре
       (ключ = 'name'), и в словаре у данного элемента параметр 'type' должен соответствовать значению 'city'. Кроме
        того, поиск городов осуществляется только в элементе словаря, у которого параметр 'group' соответствует
         значению 'CITY_GROUP'.
         Наименование страны, куда принадлежит введенный пользователем город, при наличии возможности, сокращается,
          например, United States of America = USA.
    Ключ нового нового словаря: идентификационный номер город, значение ключа: наименование города.
    Функция передает вновь созданный словарь далее. В случае отсутствия хотя бы одного города с переданным названием,
     функция передаст пустой словарь.

    :param city: наименование города (str)
    :param api_key: ключ доступа на хост
    :param local: код языка
    :return: словарь с идентификационными номерами городов и их названиями городов (Dict)
    """
    cities = dict()
    url = "https://hotels4.p.rapidapi.com/locations/search"
    querystring = {'query': city, 'locale': local}
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'hotels4.p.rapidapi.com'
        }
    print('Запрос города:', city)
    response = requests.request('GET', url, headers=headers, params=querystring)
    data = json.loads(response.text)
    if data.get('suggestions'):
        for suggestion in data.get('suggestions'):
            if suggestion.get('group') == 'CITY_GROUP':
                for elem in suggestion.get('entities', 0):
                    if elem.get('type').lower() == 'city':
                        current_city_name = re.sub(r'<.+?>', '', elem['caption'])
                        city_full_name = current_city_name.split(',')
                        length = len(city_full_name)
                        country_name = city_full_name[length - 1]
                        if len([symbol for symbol in country_name if symbol.isupper()]) > 1:
                            city_full_name[length - 1] = re.sub(r'[a-z ]', '', country_name)
                        city_full_name = ', '.join(city_full_name)
                        cities[elem['destinationId']] = city_full_name
                break
    return cities
