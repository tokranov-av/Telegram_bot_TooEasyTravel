from typing import Dict


class User:
    """
    Класс - "User" (пользователь), обеспечивающий хранение данных пользователя в ходе выполнения поиска

    Args:
         user_id (int): идентификационный номер пользователя
    Arguments:
        self.flag_search (bool): флаг информирующий о том, что какой вид поиска был выбрал пользователем, либо о том,
         что выбор еще не осуществлен. Возможные значения аргумента:
              'NOT_CHOSEN' - выбор еше не осуществлен (значение по умолчанию)
              'LOW_PRICE' - выбран поиск наиболее бюджетных отелей в выбранном городе
              'HIGH_PRICE' - выбран поиск наиболее дорогих отелей в выбранном городе
              'BEST_DEAL' - выбран поиск отелей, наиболее подходящих по цене и расположению от центра (наиболее
                            дешёвые и расположены ближе всего к центру)
        self.current_city_id (str) - идентификационный номер города, в котором будет осуществляться поиск отелей. Данный
                                    номер передается с API сайта hotels.com
        self.result_cities (Dict) - словарь, в котором ключи - идентификационные номера городов, значения ключей -
                                    наименования городов и их расположение
        self.minimum_price (float) - минимальная стоимость, необходимая для снятия номера на ночь в рублях
        self.maximum_price (float) - максимальная стоимость, необходимая для снятия номера на ночь в рублях
        self.minimum_distance (float) - минимальная дистанция от центра до отеля в километрах
        self.maximum_distance (float) - максимальная дистанция от центра до отеля в километрах
    """

    def __init__(self, user_id: int) -> None:
        self.__user_id = user_id
        self.__flag_search, self.__current_city_id, self.__message_id = 'NOT_CHOSEN', '', 0
        self.__minimum_price, self.__maximum_price, self.__minimum_distance, self.__maximum_distance = 0, 0, 0, 0
        self.__result_cities = dict()

    @property
    def flag_search(self) -> str:
        return self.__flag_search

    @flag_search.setter
    def flag_search(self, value: str) -> None:
        self.__flag_search = value

    @property
    def current_city_id(self) -> str:
        return self.__current_city_id

    @current_city_id.setter
    def current_city_id(self, value: str) -> None:
        self.__current_city_id = value

    @property
    def minimum_price(self) -> float:
        return self.__minimum_price

    @minimum_price.setter
    def minimum_price(self, value: float) -> None:
        self.__minimum_price = value

    @property
    def maximum_price(self) -> float:
        return self.__maximum_price

    @maximum_price.setter
    def maximum_price(self, value: float) -> None:
        self.__maximum_price = value

    @property
    def minimum_distance(self) -> float:
        return self.__minimum_distance

    @minimum_distance.setter
    def minimum_distance(self, value: float) -> None:
        self.__minimum_distance = value

    @property
    def maximum_distance(self) -> float:
        return self.__maximum_distance

    @maximum_distance.setter
    def maximum_distance(self, value: float) -> None:
        self.__maximum_distance = value

    @property
    def result_cities(self) -> Dict:
        return self.__result_cities

    @result_cities.setter
    def result_cities(self, value: Dict) -> None:
        self.__result_cities = value

    @property
    def message_id(self) -> int:
        return self.__message_id

    @message_id.setter
    def message_id(self, value: int) -> None:
        self.__message_id = value
