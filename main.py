import logging
import telebot
from decouple import config
from telebot import types
from bot.bestdeal import hotel_search_range
from bot.function import at_first, after_failure, get_user, user_logging, checking_numbers
from bot.locations_search import city_search
from bot.low_high_price import hotel_search_sort
from bot.user import User

bot_token = config('BOT_TOKEN')
api_key = config('API_KEY')
bot = telebot.TeleBot(bot_token)
users = dict()
help_message = ('<b>/lowprice — отображение наиболее бюджетных отелей в выбранном городе\n'
                '/highprice — отображение наиболее дорогостоящих отелей в выбранном городе\n'
                '/bestdeal — отображение отелей, наиболее подходящих по цене и расположению от центра (наиболее'
                ' дешёвые и расположены ближе всего к центру)</b\n>')


@bot.message_handler(commands=['start'])
@user_logging
def start(message: telebot.types.Message) -> None:
    """
    Функция обработки команды start. При каждом поступлении команды создается экземпляр класса User, где будут храниться
     данные о текущим пользователе. Экземпляры класса хранятся в словаре users, где ключ в словаре - это id пользователя
      в телеграмме, значение ключа - экземпляр класса с данными о соответствующем пользователе

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    users[str(message.from_user.id)] = User(message.from_user.id)
    send_message = ('<b>Привет {}!  Я — бот туристического агентства Too Easy Travel.\n\nПомогу найти:\n'
                    '💸  топ самых дешёвых отелей — /lowprice\n'
                    '💰  топ самых дорогих отелей — /highprice\n'
                    '💎  топ отелей, наиболее подходящих по цене и'
                    ' расположению — /bestdeal</b\n>'.format(message.from_user.first_name))
    bot.send_message(chat_id=message.chat.id, text=send_message, parse_mode='html')
    bot.send_message(chat_id=message.chat.id, text='<b>Ожидаю Ваш выбор...</b\n>', parse_mode='html')


@bot.message_handler(content_types=['text'])
@user_logging
def get_text_messages(message: telebot.types.Message) -> None:
    """
    Функция, обрабатывающая текстовые сообщения от пользователя. В зависимости от введенного пользователем сообщения,
     выполняется один из трех веток алгоритма программы, или выводиться информационное сообщение о командах.
    В случае отсутствия данных в словаре users о текущем пользователе, функция создает экземпляр класса с данными
     о текущем пользователе и выполняется вновь

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)

    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        if message.text.lower() == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
        elif message.text.lower() in ['/lowprice', '/highprice', '/bestdeal']:
            bot.send_message(chat_id=message.from_user.id,
                             text='<b>В каком городе ищем?</b\n>',
                             parse_mode='html')
            if message.text.lower() == '/lowprice':
                current_user.flag_search = 'LOW_PRICE'
            elif message.text.lower() == '/highprice':
                current_user.flag_search = 'HIGH_PRICE'
            elif message.text.lower() == '/bestdeal':
                current_user.flag_search = 'BEST_DEAL'
            bot.register_next_step_handler(message=message, callback=get_city_name)
        else:
            current_user.flag_search = 'NOT_CHOSEN'
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')


@user_logging
def get_city_name(message: telebot.types.Message) -> None:
    """
    Функция, определяющая id города, в котором требуется найти информацию об отелях.
    Алгоритм функции:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода: в названии города должны присутствовать только
         буквы английского алфавита и знак пробела. Если введена одна из команд /lowprice, /highprice, /bestdeal -
          выполняется поиск с начального этапа, при вводе команды /help выводиться информационное сообщение о командах;
        - после прохождения контроля ввода определяется код языка, после чего выполняется запрос на API сайта
         hotels.com с помощью функции city_search;
        - при наличии города или городов со введенным названием, пользователю выводится список городов в виде Inline
         клавиатуры для выбора нужного города, после чего id города сохраняется в переменной current_city_id экземпляра
          класса User. При наличии только одного города, результат сразу выводится сообщением и id города также
           сохраняется в экземпляре класса User;
        - выполняется следующая функция в зависимости от значения переменной flag_search экземпляра класса User;
        - при отсутствии городов со введенным названием функция get_city_name выполняется повторно.

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)

    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message.lower() in ['/lowprice', '/highprice', '/bestdeal']:
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_city_name)
        else:
            letters = 'abcdefghijklmnopqrstuvwxyz- абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
            current_message = ''.join([symbol for symbol in current_message if symbol in letters])

            if all([True if symbol in letters[26:] else False for symbol in current_message]):
                current_local = 'ru_RU'
            elif all([True if symbol in letters[:28] else False for symbol in current_message]):
                current_local = 'en_US'
            else:
                current_local = 'ERROR'

            if current_local == 'ERROR':
                bot.send_message(chat_id=message.from_user.id,
                                 text='<b>Название города введено не верно, повторите пожалуйста попытку</b\n>',
                                 parse_mode='html')
                bot.register_next_step_handler(message=message, callback=get_city_name)
            else:
                bot.send_message(chat_id=message.chat.id, text='<b>Ищу города с данным названием...</b\n>',
                                 parse_mode='html')
                current_user.result_cities = city_search(current_message, api_key=api_key, local=current_local)

                if len(current_user.result_cities) > 0:  # Проверяем результат поиска городов со введенным названием
                    if len(current_user.result_cities) > 1:
                        keyboard = types.InlineKeyboardMarkup()  # Если нашли больше одного города, создаем клавиатуру
                        for destination_id, city in current_user.result_cities.items():
                            keyboard.add(types.InlineKeyboardButton(text=f'{city}', callback_data=f'{destination_id}'))
                        current_user.message_id = message.message_id  # Защита при сбоях программы или поиска сначала
                        bot.send_message(chat_id=message.from_user.id, text=f'<b>Выберите город из списка:</b\n>',
                                         parse_mode='html', reply_markup=keyboard)
                    else:  # Если только один город, сразу выводим
                        for destination_id, city in current_user.result_cities.items():
                            current_user.current_city_id = destination_id
                            bot.send_message(chat_id=message.chat.id, text='<b>Результат поиска:</b\n>',
                                             parse_mode='html')
                            bot.send_message(chat_id=message.chat.id, text=f'<b>{city}</b\n>', parse_mode='html')
                        if current_user.flag_search in ['LOW_PRICE', 'HIGH_PRICE']:
                            bot.send_message(chat_id=message.chat.id,
                                             text='<b>Сколько гостиниц найти? (не более 25)</b\n>',
                                             parse_mode='html')
                        elif current_user.flag_search == 'BEST_DEAL':
                            bot.send_message(chat_id=message.chat.id,
                                             text='<b>Введите минимальную стоимость одной ночи в рублях</b\n>',
                                             parse_mode='html')
                    if current_user.flag_search in ['LOW_PRICE', 'HIGH_PRICE']:  # Переходим на соответствующую ветку
                        bot.register_next_step_handler(message=message, callback=get_number_of_hotels)
                    elif current_user.flag_search == 'BEST_DEAL':
                        bot.register_next_step_handler(message=message, callback=get_minimum_price)
                else:
                    bot.send_message(chat_id=message.from_user.id,
                                     text='<b>Не нашел подходящих вариантов.\nПопробуйте ещё раз.'
                                          ' В каком городе ищем?</b\n>',
                                     parse_mode='html')
                    bot.register_next_step_handler(message=message, callback=get_city_name)


@bot.callback_query_handler(func=lambda call: True)
@user_logging
def callback_worker(call: telebot.types.CallbackQuery) -> None:
    """
    Функция обработки кнопок с названиями городов. При нажатии кнопок объект call возвращает соответствующий кнопке
     идентификационный номер города, который присваивается переменной current_city_id экземпляра класса.
     В случае отсутствия данного пользователя в базе, пользователь добавляется в базу, далее выполняется функция
      get_text_messages

    :param call: объект из Bot API, содержащий в себе идентификационный номер выбранного города
    """
    current_user = get_user(call.message.chat.id, users)
    if current_user == 'NO_USER':
        users[str(call.message.chat.id)] = User(call.message.chat.id)
        bot.send_message(chat_id=call.message.chat.id,
                         text='<b>Произошел сбой работы.\nПожалуйста, выберите повторно одну из видов поиска:</b\n>',
                         parse_mode='html')
        bot.send_message(chat_id=call.message.chat.id, text=f'<b>{help_message}</b\n>', parse_mode='html')
        bot.send_message(chat_id=call.message.chat.id, text='<b>Ожидаю Ваш выбор...</b\n>', parse_mode='html')
        bot.register_next_step_handler(message=call.message, callback=get_text_messages)
    else:
        if current_user.message_id + 2 == call.message.message_id:
            current_user.current_city_id = call.data
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=None)
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'<b>{current_user.result_cities[current_user.current_city_id]}</b\n>',
                             parse_mode='html')
            if current_user.flag_search in ['LOW_PRICE', 'HIGH_PRICE']:
                bot.send_message(chat_id=call.message.chat.id, text='<b>Сколько гостиниц найти? (не более 25)</b\n>',
                                 parse_mode='html')
            elif current_user.flag_search == 'BEST_DEAL':
                bot.send_message(chat_id=call.message.chat.id,
                                 text='<b>Введите минимальную стоимость одной ночи в рублях</b\n>',
                                 parse_mode='html')
        else:  # Если id callback не соответствует ожидаемому, убираем данную клавиатуру
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=None)


@user_logging
def get_number_of_hotels(message: telebot.types.Message) -> None:
    """
    Функция, необходимая для определения количества отелей и выдающая пользователю полученные данные об отелях:
     наименование, цену снятия номера на ночь и дистанцию от центра до отеля (при поиске по команде /bestdeal).
    Алгоритм работы:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода: в сообщении должны присутствовать только
         цифры. Если введена одна из команд /lowprice, /highprice, /bestdeal - выполняется поиск с начального этапа,
          при вводе команды /help выводиться информационное сообщение о командах;
        - выполняется запрос на API сайта hotels.com с помощью функции hotel_search_sort или hotel_search_range в
         зависимости вида выполняемого поиска;
        - в случае наличия отелей, результат выводиться пользователю, иначе выполняется повторный поиск

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)

    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message in ['/lowprice', '/highprice', '/bestdeal']:
            current_user.message_id = message.message_id
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_number_of_hotels)
        elif not current_message.isdigit():
            bot.send_message(message.from_user.id, '<b>Пожалуйста, введите количество отелей в виде числа</b\n>',
                             parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_number_of_hotels)
        else:
            number_of_hotels = int(message.text)
            if number_of_hotels > 25:  # Максимальное количество отелей не более 25
                number_of_hotels = 25
            result_hotels = dict()
            bot.send_message(chat_id=message.from_user.id, text=f'<b>Ищу гостиницы...</b\n>', parse_mode='html')
            if current_user.flag_search == 'LOW_PRICE':
                result_hotels = hotel_search_sort(quantity=number_of_hotels,
                                                  city_id=int(current_user.current_city_id),
                                                  api_key=api_key,
                                                  search_kind='PRICE')
            elif current_user.flag_search == 'HIGH_PRICE':
                result_hotels = hotel_search_sort(quantity=number_of_hotels,
                                                  city_id=current_user.current_city_id,
                                                  api_key=api_key,
                                                  search_kind='PRICE_HIGHEST_FIRST')
            elif current_user.flag_search == 'BEST_DEAL':
                result_hotels = hotel_search_range(quantity=number_of_hotels,
                                                   city_id=current_user.current_city_id,
                                                   minimum_price=current_user.minimum_price,
                                                   maximum_price=current_user.maximum_price,
                                                   minimum_distance=current_user.minimum_distance,
                                                   maximum_distance=current_user.maximum_distance,
                                                   api_key=api_key)
            if len(result_hotels) > 0:
                bot.send_message(message.chat.id, '<b>Результат:</b\n>', parse_mode='html')
                if current_user.flag_search in ['LOW_PRICE', 'HIGH_PRICE']:
                    for name, value in result_hotels.items():
                        bot.send_message(chat_id=message.chat.id,
                                         text=f'<b>{name}\nАдрес: {value[0]}\nСтоимость от {value[1]} рублей'
                                              f' за ночь </b\n>',
                                         parse_mode='html')
                elif current_user.flag_search == 'BEST_DEAL':
                    for name, value in result_hotels.items():
                        bot.send_message(chat_id=message.chat.id,
                                         text=f'<b>{name}\nАдрес: {value[0]}\nСтоимость от {value[1]} рублей за ночь\n'
                                              f'Расстояние от центра составляет {value[2]} км</b\n>', parse_mode='html')
                current_user.flag_search = 'NOT_CHOSEN'
            else:
                bot.send_message(chat_id=message.from_user.id,
                                 text='<b>Не нашел подходящих вариантов.\nПопробуйте ещё раз.</b\n>', parse_mode='html')
                if current_user.flag_search in ['LOW_PRICE', 'HIGH_PRICE']:
                    bot.register_next_step_handler(message=message, callback=get_city_name)
                else:
                    bot.send_message(chat_id=message.from_user.id,
                                     text='<b>Введите минимальную стоимость одной ночи в рублях</b\n>',
                                     parse_mode='html')
                    bot.register_next_step_handler(message=message, callback=get_minimum_price)


@user_logging
def get_minimum_price(message: telebot.types.Message) -> None:
    """
    Функция получения минимальной стоимости за ночевку в номере гостиницы
    Алгоритм работы:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода:
          а) если введена одна из команд /lowprice, /highprice, /bestdeal -  выполняется поиск отелей с начального
           этапа, при вводе команды /help выводиться информационное сообщение о командах;
          б) если отсутствуют вышеперечисленные команды, проверку корректности ввода осуществляет функция
           checking_numbers, после чего, в случае ожидаемого ввода, переменной minimum_price экземпляра класса User
            присваивается введенное значение, и далее, выполняется  get_maximum_price. в случае ошибки ввода, функция
             get_minimum_price выполняется вновь.

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)
    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message in ['/lowprice', '/highprice', '/bestdeal']:
            current_user.message_id = message.message_id
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_minimum_price)
        else:
            checking_numbers(current_bot=bot, current_message=message, instance=current_user,
                             next_step=get_maximum_price, error_next_step=get_minimum_price,
                             output_message='Введите максимальную стоимость одной ночи в рублях',
                             error_output_message='Стоимость необходимо ввести в виде числа, пожалуйста,'
                                                  ' повторите попытку', variable='MINIMUM_PRICE')


@user_logging
def get_maximum_price(message: telebot.types.Message) -> None:
    """
    Функция получения максимальной стоимости за ночевку в номере гостиницы
    Алгоритм работы:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода:
          а) если введена одна из команд /lowprice, /highprice, /bestdeal -  выполняется поиск отелей с начального
           этапа, при вводе команды /help выводиться информационное сообщение о командах;
          б) если отсутствуют вышеперечисленные команды, проверку корректности ввода осуществляет функция
           checking_numbers, после чего, в случае ожидаемого ввода, переменной maximum_price экземпляра класса User
            присваивается введенное значение, и далее, выполняется  get_minimum_distance. в случае ошибки ввода,
             функция get_maximum_price выполняется вновь.

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)
    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message in ['/lowprice', '/highprice', '/bestdeal']:
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_maximum_price)
        else:
            checking_numbers(current_bot=bot, current_message=message, instance=current_user,
                             next_step=get_minimum_distance, error_next_step=get_maximum_price,
                             output_message='Введите минимальное расстояние от центра в километрах',
                             error_output_message='Стоимость необходимо ввести в виде числа, пожалуйста, повторите'
                                                  ' попытку', variable='MAXIMUM_PRICE')


@user_logging
def get_minimum_distance(message: telebot.types.Message) -> None:
    """
    Функция получения минимальной дистанции от центра до отеля
    Алгоритм работы:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода:
          а) если введена одна из команд /lowprice, /highprice, /bestdeal -  выполняется поиск отелей с начального
           этапа, при вводе команды /help выводиться информационное сообщение о командах;
          б) если отсутствуют вышеперечисленные команды, проверку корректности ввода осуществляет функция
           checking_numbers, после чего, в случае ожидаемого ввода, переменной minimum_distance экземпляра класса User
            присваивается введенное значение, и далее, выполняется  get_maximum_distance. в случае ошибки ввода,
             функция get_minimum_distance выполняется вновь.

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)

    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message in ['/lowprice', '/highprice', '/bestdeal']:
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_minimum_distance)
        else:
            checking_numbers(current_bot=bot, current_message=message, instance=current_user,
                             next_step=get_maximum_distance, error_next_step=get_minimum_distance,
                             output_message='Введите максимальное расстояние от центра в километрах',
                             error_output_message='Расстояние необходимо ввести в виде числа, пожалуйста, повторите'
                                                  ' попытку', variable='MINIMUM_DISTANCE')


@user_logging
def get_maximum_distance(message: telebot.types.Message) -> None:
    """
    Функция получения максимальной дистанции от центра до отеля
    Алгоритм работы:
        - получение экземпляра класса о текущем пользователе из словаря. При отсутствии данных создается экземпляр
         класса на текущего пользователя и программа выполняется с начального этапа;
        - при наличии экземпляра класса осуществляется контроль ввода:
          а) если введена одна из команд /lowprice, /highprice, /bestdeal -  выполняется поиск отелей с начального
           этапа, при вводе команды /help выводиться информационное сообщение о командах;
          б) если отсутствуют вышеперечисленные команды, проверку корректности ввода осуществляет функция
           checking_numbers, после чего, в случае ожидаемого ввода, переменной maximum_distance экземпляра класса User
            присваивается введенное значение, и далее, выполняется  get_number_of_hotels. в случае ошибки ввода,
             функция get_maximum_distance выполняется вновь.

    :param message: объект из Bot API, содержащий в себе информацию о сообщении и данные о пользователе
    """
    current_user = get_user(message.from_user.id, users)

    if current_user == 'NO_USER':
        users[str(message.from_user.id)] = User(message.from_user.id)
        after_failure(current_bot=bot, current_message=message, next_step=get_text_messages)
    else:
        current_message = message.text.lower()
        if current_message in ['/lowprice', '/highprice', '/bestdeal']:
            at_first(current_bot=bot, current_message=message, instance=current_user, next_step=get_city_name)
        elif current_message == '/help':
            bot.send_message(chat_id=message.from_user.id, text=help_message, parse_mode='html')
            bot.register_next_step_handler(message=message, callback=get_maximum_distance)
        else:
            checking_numbers(current_bot=bot, current_message=message, instance=current_user,
                             next_step=get_number_of_hotels, error_next_step=get_maximum_distance,
                             output_message='Сколько гостиниц найти? (не более 25)',
                             error_output_message='Расстояние необходимо ввести в виде числа, пожалуйста,'
                                                  ' повторите попытку', variable='MAXIMUM_DISTANCE')


logging.basicConfig(filename='log_file.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

while True:
    try:
        print('<<< Бот "Too Easy Travel" работает>>>')
        bot.polling(none_stop=True, interval=0)
    except Exception as error_message:
        logging.exception(error_message)
