import functools
import logging
from typing import Dict, List, Callable, Type, Tuple, Any
import telebot
from bot.user import User


def hotel_search(data: Dict, quantity: int) -> Dict[str, List]:
    """
    Функция копирования в новый словарь hotels наименования отелей и стоимости снятия одного номера на ночь в копируемом
     отеле из переданного словаря data с известной структурой. Ключи в новом словаре - наименования отелей,
      значения ключей - стоимости снятия номера на ночь в соответствующем отеле.
    Копирование наименования отелей продолжается до тех пор, пока их количество не приравняется переданному значению
     quantity, или функция не скопирует все наименования отелей, имеющиеся в переданном словаре data

    :param data: передаваемый словарь (Dict)
    :param quantity: количество запрашиваемых отелей (int)
    :return hotels: итоговый словарь с наименованиями отелей (int)
    """
    hotels = dict()
    if data.get('data').get('body').get('searchResults').get('results'):
        for element in data.get('data').get('body').get('searchResults').get('results'):
            if len(hotels) < quantity:
                if element.get('ratePlan') is not None and element.get('address') is not None:
                    postal_code = element.get('address').get('postalCode')
                    street_address = element.get('address').get('streetAddress')
                    locality = element.get('address').get('locality')
                    region = element.get('address').get('region')
                    country_name = element.get('address').get('countryName')
                    if region == locality or locality == '':
                        full_address = [postal_code, street_address, region, country_name]
                    elif region == '':
                        full_address = [postal_code, street_address, locality, country_name]
                    else:
                        full_address = [postal_code, street_address, locality, region, country_name]
                    full_address = ', '.join([value for value in full_address if value is not None])
                    current_price = element.get('ratePlan').get('price').get('exactCurrent')
                    hotels[element.get('name')] = [full_address, current_price]
            else:
                break
    return hotels


def hotel_search_distance(data: Dict, quantity: int, distance_minimum: float, distance_maximum: float,
                          price_min: float, price_max: float) -> Tuple[Dict[str, List[float]], float]:
    """
    Функция копирования в новый словарь hotels наименования отелей, стоимости снятия одного номера на ночь и дистанции
     от центра до копируемого отеля из переданного словаря data с известной структурой. Ключи в новом словаре -
      наименования отелей, значения ключей - список, где элемент с индексом "0" - стоимость снятия номера на ночь,
       элемент с индексом "1" - дистанция от центра до данного отеля.
    Копирование наименования отелей продолжается до тех пор, пока их количество не станет равной переданному значению
     quantity, или функция не скопирует все наименования отелей, имеющиеся в переданном словаре data.
    Добавление в новый словарь выполняется только при выполнения условия: стоимость одной ночи должно входит в
     переданный диапазон цен, и расстояние от центра до отеля должно входить в переданный диапазон расстояний.
      Предполагается, что цена снятия номера на одну ночь и расстояние от центра до отеля имеются в передаваемом словаре

    :param data: передаваемый извне словарь (Dict)
    :param quantity: количество запрашиваемых отелей (int)
    :param distance_minimum: минимальная дистанция от центра до отеля (float)
    :param distance_maximum: максимальная дистанция от центра до отеля (float)
    :param price_min: минимальная стоимость снятия номера на одну ночь (float)
    :param price_max: минимальная стоимость снятия номера на одну ночь (float)
    :return: итоговый словарь с наименованиями отелей (Dict)
    """
    hotels = dict()
    price_high = 0
    for element in data.get('data').get('body').get('searchResults').get('results'):
        if (element.get('landmarks') is not None and element.get('ratePlan') is not None and
                element.get('address') is not None):
            current_distance = element.get('landmarks')[0].get('distance').split()[0]
            if ',' in current_distance:
                current_distance = current_distance.replace(',', '.')
            current_distance = float(current_distance)
            postal_code = element.get('address').get('postalCode')
            street_address = element.get('address').get('streetAddress')
            locality = element.get('address').get('locality')
            region = element.get('address').get('region')
            country_name = element.get('address').get('countryName')
            if region == locality or locality == '':
                full_address = [postal_code, street_address, region, country_name]
            elif region == '':
                full_address = [postal_code, street_address, locality, country_name]
            else:
                full_address = [postal_code, street_address, locality, region, country_name]
            full_address = ', '.join(full_address)
            price_high = current_price = element.get('ratePlan').get('price').get('exactCurrent')
            if (len(hotels) < quantity and distance_minimum <= current_distance <= distance_maximum and
                    price_min <= current_price <= price_max):
                hotels[element.get('name')] = [full_address, current_price, current_distance]
    return hotels, price_high


def after_failure(current_bot: telebot.TeleBot, current_message: telebot.types.Message, next_step: Callable) -> None:
    """
    Функция восстановления работы с пользователем в случае сбоя работы программы чат-бота (в случае отсутствия
     экземпляра класса USER в базе данных программы).

    :param current_bot: текущий бот телеграмм
    :param current_message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    :param next_step: функция, передаваемая для выполнения в следующем шаге после выполнения текущей функции
    """
    help_m = ('<b>/lowprice — отображение наиболее бюджетных отелей в выбранном городе\n'
              '/highprice — отображение наиболее дорогостоящих отелей в выбранном городе\n'
              '/bestdeal — отображение отелей, наиболее подходящих по цене и расположению от центра (наиболее'
              ' дешёвые и расположены ближе всего к центру)</b\n>')

    current_bot.send_message(chat_id=current_message.from_user.id,
                             text='<b>Произошел сбой.\nПожалуйста, выберите повторно одну из видов поиска:</b\n>',
                             parse_mode='html')
    current_bot.send_message(chat_id=current_message.from_user.id, text=f'<b>{help_m}</b\n>', parse_mode='html')
    current_bot.send_message(chat_id=current_message.chat.id, text='<b>Ожидаю Ваш выбор...</b\n>', parse_mode='html')
    current_bot.register_next_step_handler(message=current_message, callback=next_step)


def at_first(current_bot: telebot.TeleBot, current_message: telebot.types.Message,
             instance: Type[User], next_step: Callable) -> None:
    """
    Функция возврата в начальный этап поиска, т.е. выбора вида поиска в случае пожелания пользователя изменить
     вид поиска

    :param current_bot: текущий бот телеграмм
    :param current_message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    :param instance: экземпляр класса, где содержаться данные о текущем пользователе
    :param next_step: функция, которая передается для выполнения в следующем шаге после выполнения текущей функции
    """
    current_bot.send_message(chat_id=current_message.chat.id, text='<b>Начинаем поиск сначала</b\n>', parse_mode='html')
    current_bot.send_message(chat_id=current_message.from_user.id,
                             text='<b>В каком городе ищем?</b\n>',
                             parse_mode='html')
    message_low = current_message.text.lower()
    if message_low == '/lowprice':
        instance.flag_search = 'LOW_PRICE'
    elif message_low == '/highprice':
        instance.flag_search = 'HIGH_PRICE'
    elif message_low == '/bestdeal':
        instance.flag_search = 'BEST_DEAL'
    current_bot.register_next_step_handler(message=current_message, callback=next_step)


def get_user(user_message: int, data: Dict) -> Type[User] or str:
    """
    Функция поиска значения передаваемого ключа в передаваемом словаре. В случае отсутствия значения ключа функция
     возвращает строку 'NO_USER'

    :param user_message: ключ словаря, в данном случа - это id пользователя
    :param data: словарь, где ключи - id пользователей, значения ключей - экземпляры класса пользователей
    :return: экземпляр класса или строка 'No_USER'
    """
    current_user = data.get(str(user_message))
    if current_user is not None:
        return current_user
    else:
        return 'NO_USER'


def user_logging(user_func: Callable) -> Callable:
    """
    Декоратор логирования переданной функции
    Перед выполнением наименование функции записывается в файл log_file.log.

    :param user_func: передаваемая пользователем функция
    :return: wrapped_func
    """

    @functools.wraps(user_func)
    def wrapped_func(*args, **kwargs) -> Any:
        logging.basicConfig(filename='log_file.log', level=logging.INFO,
                            filemode='w', format='%(asctime)s - %(message)s')
        logging.info(f'The function is called: {user_func.__name__}')
        return user_func(*args, **kwargs)

    return wrapped_func


def checking_numbers(current_bot: telebot.TeleBot, current_message: telebot.types.Message, instance: Type[User],
                     next_step: Callable, error_next_step: Callable,
                     output_message: str, error_output_message: str, variable: str) -> None:
    """
    Функция контроля соответствия введенного значения числам. Функция предназначена работы с переменными класса User
     в рамках данной программы.
     В сообщении должны присутствовать только цифры, знак запятой или знак точки. Если сообщение введено верно,
      строка преобразовывается в тип float,и присваивается соответствующей переменной экземпляра класса, которая
       определяется передаваемым параметром variable.

    :param current_bot: текущий бот телеграмм
    :param current_message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    :param instance: экземпляр класса, где содержаться данные о текущем пользователе
    :param next_step: функция, которая передается для выполнения в следующем шаге после выполнения текущей функции
    :param error_next_step: функция, которая передается для выполнения в следующем шаге после обнаружения ошибки ввода
    :param output_message: сообщение, выводимое пользователю перед выполнением функции, указанной в параметре next_step
    :param error_output_message: сообщение, выводимое пользователю после обнаружения ошибки ввода
    :param variable: параметр, информирующий о текущей переменной экземпляра класса
    """
    numbers = '0123456789.'
    user_message = current_message.text.lower()
    if ',' in user_message:
        user_message = user_message.replace(',', '.')
    if user_message.count('.') <= 1 and all([True if symbol in numbers else False for symbol in user_message]):
        if variable == 'MINIMUM_PRICE':
            instance.minimum_price = int(user_message)
        elif variable == 'MAXIMUM_PRICE':
            instance.maximum_price = int(user_message)
            if instance.minimum_price > instance.maximum_price:
                instance.minimum_price, instance.maximum_price = instance.maximum_price, instance.minimum_price
        elif variable == 'MINIMUM_DISTANCE':
            instance.minimum_distance = float(user_message)
        elif variable == 'MAXIMUM_DISTANCE':
            instance.maximum_distance = float(user_message)
            if instance.minimum_distance > instance.maximum_distance:
                instance.minimum_distance, instance.maximum_distance = \
                    instance.maximum_distance, instance.minimum_distance
        current_bot.send_message(chat_id=current_message.chat.id, text=f'<b>{output_message}</b\n>', parse_mode='html')
        current_bot.register_next_step_handler(message=current_message, callback=next_step)
    else:
        current_bot.send_message(chat_id=current_message.from_user.id, text=f'<b>{error_output_message}</b\n>',
                                 parse_mode='html')
        current_bot.register_next_step_handler(message=current_message, callback=error_next_step)
