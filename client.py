import sys
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM
from errors import UsernameTooLongError, ResponseCodeLenError, MissingKeyError, ResponseCodeError
from jim.config import *
from jim.utils import send_message, get_message
import logging
import log.log_configs.client_log_config
from log.decorators import Log

client_logger = logging.getLogger('client_logger')
log_it = Log(client_logger)


def get_time():
    """
    Функция возвращает текущее время
    :return: str (HH:MM:SS)
    """
    return datetime.now().strftime("%H:%M:%S")


@log_it
def create_presence_message(account_name=DEFAULT_ACCOUNT_NAME):
    """
    Функция формирует сообщение присутствия
    :param account_name: str (Имя пользователя)
    :return: dict (Сообщение присутствия)
    """
    if not isinstance(account_name, str):
        raise TypeError
    if len(account_name) > MAX_USERNAME_LEN:
        raise UsernameTooLongError(account_name)
    presence_message = {
        ACTION: PRESENCE,
        TIME: get_time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return presence_message


@log_it
def check_server_message(response_message):
    if not isinstance(response_message, dict):
        raise TypeError
    if RESPONSE not in response_message:
        raise MissingKeyError(RESPONSE)
    response_code = response_message[RESPONSE]
    if len(str(response_code)) != RESPONSE_CODE_LEN:
        raise ResponseCodeLenError(response_code)
    if response_code not in RESPONSE_CODES:
        raise ResponseCodeError(response_code)
    return response_message


if __name__ == '__main__':
    client = socket(AF_INET, SOCK_STREAM)
    try:
        addr = sys.argv[1]
    except IndexError:
        addr = DEFAULT_SERVER_ADDRESS
    try:
        port = int(sys.argv[2])
    except IndexError:
        port = DEFAULT_SERVER_PORT
    except ValueError:
        client_logger.error(f'\tФункция:\n'
                            f'\tsys.argv\n'
                            f'\tОшибка:\n'
                            f'\tПереданы некорректные аргументы - {sys.argv[1]}, {sys.argv[2]}')
        sys.exit(0)

    client.connect((addr, port))
    presence = create_presence_message('Вася')
    send_message(client, presence)
    server_response = get_message(client)
    server_response = check_server_message(server_response)
    print(server_response)
    client.close()

