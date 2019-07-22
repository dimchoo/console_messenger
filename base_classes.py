import sys
import json
from datetime import datetime
import time
from socket import socket, AF_INET, SOCK_STREAM
from errors import *
from jim.config import *
from jim.utils import send_message, get_message
import logging
import log.log_configs.client_log_config
from log.decorators import Log
from multiprocessing import Process
from threading import Thread
import argparse
import select

client_logger = logging.getLogger('client_logger')
log_client = Log(client_logger)

server_logger = logging.getLogger('server_logger')
log_server = Log(server_logger)


class BaseClient:

    @staticmethod
    def __get_time():
        """
        Метод возвращает текущее время
        :return: str (HH:MM:SS)
        """
        return datetime.now().strftime("%H:%M:%S")

    @log_client
    def __create_exit_message(self, account_name):
        """
        Метод, возвращающий словарь с сообщением о выходе
        :param account_name: str (Имя пользователя, который вышел)
        :return: dict (Словарь с сообщением о выходе)
        """
        return {
            ACTION: EXIT,
            TIME: self.__get_time(),
            ACCOUNT_NAME: account_name
        }

    @staticmethod
    @log_client
    def message_from_server(sock, my_username):
        """
        Метод-обработчик сообщений других пользователей, поступающих от сервера
        :param sock: socket (Сокет с сообщением)
        :param my_username: str (Имя клиента, для которого сообщение)
        :return: None
        """
        while True:
            try:
                message = get_message(sock)
                if ACTION in message \
                        and message[ACTION] == MESSAGE \
                        and SENDER in message \
                        and DESTINATION in message \
                        and MESSAGE_TEXT in message \
                        and message[DESTINATION] == my_username:
                    print(f'[Сообщение от "{message[SENDER]}"]:\n'
                          f'{message[MESSAGE_TEXT]}')
                    client_logger.info(
                        f'Получено сообщение от пользователя {message[SENDER]}:\n'
                        f'{message[MESSAGE_TEXT]}')
                else:
                    client_logger.error(f'Получено некорректное сообщение от сервера:\n{message}')
            except IncorrectDataReceivedError:
                client_logger.error('Не удалось декодировать полученное сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                client_logger.critical(f'Потеряно соединение с сервером')
                break

    @log_client
    def create_message(self, sock, name_from, name_to, message):
        """
        Метод создающий словарь с сообщением
        :param sock: socket (Клиентский сокет)
        :param name_from: str (Имя отправителя)
        :param name_to: str (Имя получателя)
        :param message: str (Сообщение)
        :return: None
        """
        message_dict = {
            ACTION: MESSAGE,
            SENDER: name_from,
            DESTINATION: name_to,
            TIME: self.__get_time(),
            MESSAGE_TEXT: message
        }
        client_logger.debug(f'Сформирован словарь сообщения:\n{message_dict}')
        try:
            send_message(sock, message_dict)
            client_logger.info(f'Отправлено сообщение для пользователя {name_to}')
        except (
                OSError,
                ConnectionError,
                ConnectionAbortedError,
                ConnectionResetError,
                KeyboardInterrupt,
                json.JSONDecodeError
        ):
            client_logger.critical('Потеряно соединение с сервером.')
            exit(1)

    @staticmethod
    def print_help():
        """
        Метод, выводящий на экран подсказки "help"
        :return: None
        """
        print('Поддерживаемые команды:')
        print('#help - Помощь')
        print('#exit - Выйти из чата')

    @log_client
    def user_interactive(self, sock, name_from, name_to):
        """
        Метод интерактивной работы с клиентом
        Вывод подсказок, завершение работы скрипта и отправка сообщений
        :param sock:
        :param name_from:
        :param name_to:
        :return: None
        """
        self.print_help()
        while True:
            message = input(f'[{name_from} (Вы)]:\n')
            if message == '#help':
                self.print_help()
            elif message == '#exit':
                send_message(sock, self.__create_exit_message(name_from))
                print(f'Чат завершен, {name_from} вышел')
                client_logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                self.create_message(sock, name_from, name_to, message)

    @log_client
    def create_presence(self, account_name):
        """
        Метод, возвращающий словарь с сообщением о присутствии
        :param account_name: str (Имя клиента)
        :return: dict (Словарь с сообщением о присутствии)
        """
        client_logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return {
            ACTION: PRESENCE,
            TIME: self.__get_time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }

    @staticmethod
    @log_client
    def process_response_answer(message):
        """
        Метод разбирает ответ сервера на сообщение о присутствии,
        возращает 200 если все ОК или генерирует исключение при ошибке
        :param message:
        :return: str (Ответ если все ОК)
        """
        client_logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400 : {message[ERROR]}')
        raise ReqFieldMissingError(RESPONSE)

    @staticmethod
    def arg_parser():
        """
        Метод парсит аргументы коммандной строки
        :return: адрес и порт сервера
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_SERVER_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_SERVER_PORT, type=int, nargs='?')
        # parser.add_argument('-n', '--name', default=None, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        server_address = namespace.addr
        server_port = namespace.port
        # client_name = namespace.name

        # проверим подходящий номер порта
        if not 1023 < server_port < 65536:
            client_logger.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            exit(1)

        return server_address, server_port

    def start(self):
        """
        Метод старта клиентского модуля
        :return: None
        """
        try:
            # Сообщаем о запуске
            print('Консольный месседжер запущен...')

            # Загружаем параметы коммандной строки
            server_address, server_port = self.arg_parser()

            client_name = input('Введите ваше имя:')
            receiver_name = input('Введите имя получателя: ')

            client_logger.info(
                f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
                f'порт: {server_port}, имя пользователя: {client_name}')

            # Инициализация сокета и сообщение серверу о нашем появлении
            try:
                transport = socket(AF_INET, SOCK_STREAM)
                transport.connect((server_address, server_port))
                send_message(transport, self.create_presence(client_name))
                answer = self.process_response_answer(get_message(transport))
                client_logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
                print(f'Установлено соединение с сервером...')
            except json.JSONDecodeError:
                client_logger.error('Не удалось декодировать полученный JSON-объект.')
                exit(1)
            except ServerError as error:
                client_logger.error(f'При установке соединения сервер вернул ошибку:\n{error.text}')
                exit(1)
            except ReqFieldMissingError as missing_error:
                client_logger.error(f'В ответе сервера отсутствует необходимое поле:\n{missing_error.missing_field}')
                exit(1)
            except (ConnectionRefusedError, ConnectionError):
                client_logger.critical(
                    f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                    f'конечный компьютер отверг запрос на подключение.')
                exit(1)
            else:
                # Если соединение с сервером установлено корректно, запускаем клиенский процесс приёма сообщний
                receiver = Thread(target=self.message_from_server, args=(transport, client_name))
                receiver.daemon = True
                receiver.start()

                # затем запускаем отправку сообщений и взаимодействие с пользователем.
                user_interface = Thread(target=self.user_interactive, args=(transport, client_name, receiver_name))
                user_interface.daemon = True
                user_interface.start()
                client_logger.debug('Запущены процессы')

                # Watchdog основной цикл, если один из потоков завершён,
                # то значит или потеряно соединение или пользователь
                # ввёл exit. Поскольку все события обработываются в потоках,
                # достаточно просто завершить цикл.
                while True:
                    time.sleep(1)
                    if receiver.is_alive() and user_interface.is_alive():
                        continue
                    break
        except KeyboardInterrupt:
            print(f'Чат завершен, клиент вышел')


class BaseServer:

    @staticmethod
    @log_server
    def __process_client_message(message, message_list, client, clients, names):
        """
        Метод обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости
        :param message: dict (Сообщение от клиента)
        :param message_list: list (Список с сообщениями)
        :param client: socket (Клиентский сокет)
        :param clients: list (Список клиентов)
        :param names: dict (Словарь, содержащий имена пользователей и соответствующие им сокеты)
        :return: None
        """
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_OK)
            else:
                response = RESPONSE_WRONG_REQUEST
                response[ERROR] = f'Имя "{message[USER][ACCOUNT_NAME]}" уже занято.'
                send_message(client, response)
                clients.remove(client)
                client.close()
                return
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            message_list.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            clients.remove(names[ACCOUNT_NAME])
            names[ACCOUNT_NAME].close()
            del names[ACCOUNT_NAME]
            return
        else:
            response = RESPONSE_WRONG_REQUEST
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    @staticmethod
    @log_server
    def __process_message(message, names, listen_sockets):
        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_sockets:
            send_message(names[message[DESTINATION]], message)
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_sockets:
            raise ConnectionError

    @staticmethod
    @log_server
    def __arg_parser():
        """
        Парсер аргументов коммандной строки
        :return: str & int (ip-адрес и порт)
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=DEFAULT_SERVER_PORT, type=int, nargs='?')
        parser.add_argument('-a', default=DEFAULT_BIND_IP, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        listen_address = namespace.a
        listen_port = namespace.p

        if not 1023 < listen_port < 65536:
            server_logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта {listen_port}.\n'
                f'Допустимы адреса с 1024 до 65535.')
            exit(1)

        return listen_address, listen_port

    def start(self):
        """
        Метод запуска сервера
        :return: None
        """
        listen_address, listen_port = self.__arg_parser()
        print('Сервер запущен...')
        server_logger.info(
            f'Сервер запущен!\n'
            f'Порт для подключений: {listen_port},\n'
            f'Адрес с которого принимаются подключения: {listen_address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        transport = socket(AF_INET, SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)

        clients = []
        messages = []
        names = {}

        transport.listen(MAX_CONNECTIONS_LEN)

        try:
            while True:
                try:
                    client, client_address = transport.accept()
                except OSError:
                    pass
                else:
                    server_logger.info(f'Установлено соедение с ПК {client_address}')
                    clients.append(client)

                receive_data_list = []
                send_data_list = []

                try:
                    if clients:
                        receive_data_list, send_data_list, error_list = select.select(clients, clients, [], 0)
                except OSError:
                    pass

                if receive_data_list:
                    for client_with_message in receive_data_list:
                        try:
                            self.__process_client_message(
                                get_message(client_with_message),
                                messages,
                                client_with_message,
                                clients,
                                names)
                        except Exception:
                            server_logger.info(f'Клиент {client_with_message} отключился от сервера.')
                            clients.remove(client_with_message)

                for message in messages:
                    try:
                        self.__process_message(message, names, send_data_list)
                    except Exception:
                        server_logger.info(f'Связь с клиентом "{message[DESTINATION]}" была потеряна')
                        clients.remove(names[message[DESTINATION]])
                        del names[message[DESTINATION]]
                messages.clear()
        except KeyboardInterrupt:
            print('Сервер остановлен.')
