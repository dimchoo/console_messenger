import sys
import re
from socket import socket, AF_INET, SOCK_STREAM
from jim.config import *
from jim.utils import send_message, get_message
import logging
import log.log_configs.server_log_config
from log.decorators import Log
import select

server_logger = logging.getLogger('server_logger')
log_it = Log(server_logger)


@log_it
def presence_message_response(presence_message):
    """
    Функция формирует ответ на сообщение о присутствии от клиента
    :param presence_message: dict (Словарь с сообщением о присутствии)
    :return: dict (Словарь с ответом для клиента)
    """
    time_template = r'^([0-1][0-9]|[2][0-3]):[0-5][0-9]:[0-5][0-9]$'
    if ACTION in presence_message \
            and presence_message[ACTION] == PRESENCE \
            and TIME in presence_message \
            and re.match(time_template, presence_message[TIME]) is not None:
        return {RESPONSE: OK}
    return {RESPONSE: WRONG_REQUEST, ERROR: 'Неверный запрос!'}


def read_requests(read_clients_list, all_clients_list):
    """
    Функция читает сообщения от клиентов и возвращает список с собщениями
    :param read_clients_list: list (Сокеты клиентов, которые прислали сообщения для чтения)
    :param all_clients_list: list (Все сокеты клиентов)
    :return: list (Список с собщениями)
    """
    message_list = []

    for client_socket in read_clients_list:
        try:
            client_message = get_message(client_socket)
            message_list.append(client_message)
        except Exception:
            print('Клиент отключился!')
            all_clients_list.remove(client_socket)
        return message_list


def send_responses(message_list, write_client_list, all_clients_list):
    """
    Функция отправки сообщений клиентам, ждущим сообщения
    :param message_list: list (Список сообщений от клиентов, результат функции read_requests)
    :param write_client_list: list (Сокеты клиентов, которые ждут сообщения)
    :param all_clients_list: list (Все сокеты клиентов)
    :return: None
    """
    for client_socket in write_client_list:
        try:
            for message in message_list:
                try:
                    send_message(client_socket, message)
                except Exception:
                    print('Клиент отключился!')
                    all_clients_list.remove(client_socket)
        except Exception:
            pass


if __name__ == '__main__':
    server = socket(AF_INET, SOCK_STREAM)
    try:
        addr = str(sys.argv[1])
    except IndexError:
        addr = DEFAULT_BIND_IP
    try:
        port = int(sys.argv[2])
    except IndexError:
        port = DEFAULT_SERVER_PORT
    except ValueError:
        server_logger.error(f'\tФункция:\n'
                            f'sys.argv\n'
                            f'\tОшибка:\n'
                            f'Переданы некорректные аргументы - {sys.argv[1]}, {sys.argv[2]}')
        sys.exit(0)

    server.bind((addr, port))
    server.listen(5)
    server.settimeout(1)
    clients_list = []
    try:
        while True:
            try:
                connection, addr = server.accept()
                presence = get_message(connection)
                response = presence_message_response(presence)
                send_message(connection, response)
            except OSError:
                pass
            else:
                print(f'Запрос на соединение от {addr}')
                clients_list.append(connection)
            finally:
                read_list = []
                write_list = []

            try:
                read_list, write_list, error_list = select.select(clients_list, clients_list, [], 0)
            except Exception:
                pass

            requests = read_requests(read_list, clients_list)
            send_responses(requests, write_list, clients_list)
    except KeyboardInterrupt:
        server_logger.info('\tСервер остановлен')
        print('Сервер остановлен!')
