import sys
import re
from socket import socket, AF_INET, SOCK_STREAM
from jim.config import *
from jim.utils import send_message, get_message
import logging
import log.log_configs.server_log_config

server_logger = logging.getLogger('server_logger')


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
        response_ok = {RESPONSE: OK}
        log_message = \
            f'\tФункция:\n\t{presence_message_response.__name__}\n' \
            f'\tАргумент:\n\t{presence_message}\n' \
            f'\tОтвет:\n\t{response_ok}'
        server_logger.info(log_message)
        return response_ok
    response_error = {RESPONSE: WRONG_REQUEST, ERROR: 'Неверный запрос!'}
    log_message = \
        f'\tФункция:\n\t{presence_message_response.__name__}\n' \
        f'\tАргумент:\n\t{presence_message}\n' \
        f'\tОтвет:\n\t{response_error}'
    server_logger.error(log_message)
    return response_error


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
    try:
        while True:
            client, addr = server.accept()
            presence = get_message(client)
            print(presence)
            response = presence_message_response(presence)
            send_message(client, response)
            client.close()
    except KeyboardInterrupt:
        server_logger.info('\tСервер остановлен')
        print('Сервер остановлен!')
