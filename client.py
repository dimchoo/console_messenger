import sys
from datetime import datetime
from socket import socket, AF_INET, SOCK_STREAM
from errors import UsernameTooLongError, ResponseCodeLenError, MissingKeyError, ResponseCodeError
from jim.config import *
from jim.utils import send_message, get_message
import logging
import log.log_configs.client_log_config

client_logger = logging.getLogger('client_logger')


def get_time():
    """
    Функция возвращает текущее время
    :return: str (HH:MM:SS)
    """
    return datetime.now().strftime("%H:%M:%S")


def create_presence_message(account_name=DEFAULT_ACCOUNT_NAME):
    """
    Функция формирует сообщение присутствия
    :param account_name: str (Имя пользователя)
    :return: dict (Сообщение присутствия)
    """
    if not isinstance(account_name, str):
        log_message = \
            f'\tФункция:\n\t{create_presence_message.__name__}\n' \
            f'\tАргумент:\n\t{account_name}\n' \
            f'\tОшибка:\n\t{TypeError}'
        client_logger.error(log_message)
        raise TypeError
    if len(account_name) > MAX_USERNAME_LEN:
        log_message = \
            f'\tФункция:\n\t{create_presence_message.__name__}\n' \
            f'\tАргумент:\n\t{account_name}\n' \
            f'\tОшибка:\n\t{UsernameTooLongError}'
        client_logger.error(log_message)
        raise UsernameTooLongError(account_name)
    presence_message = {
        ACTION: PRESENCE,
        TIME: get_time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    log_message = \
        f'\tФункция:\n\t{create_presence_message.__name__}\n' \
        f'\tАргумент:\n\t{account_name}\n' \
        f'\tОтвет:\n\t{presence_message}'
    client_logger.info(log_message)
    return presence_message


def check_server_message(response_message):
    if not isinstance(response_message, dict):
        log_message = \
            f'\tФункция:\n\t{check_server_message.__name__}\n' \
            f'\tАргумент:\n\t{response_message}\n' \
            f'\tОшибка:\n\t{TypeError}'
        client_logger.error(log_message)
        raise TypeError
    if RESPONSE not in response_message:
        log_message = \
            f'\tФункция:\n\t{check_server_message.__name__}\n' \
            f'\tАргумент:\n\t{response_message}\n' \
            f'\tОшибка:\n\t{MissingKeyError}'
        client_logger.error(log_message)
        raise MissingKeyError(RESPONSE)
    response_code = response_message[RESPONSE]
    if len(str(response_code)) != RESPONSE_CODE_LEN:
        log_message = \
            f'\tФункция:\n\t{check_server_message.__name__}\n' \
            f'\tАргумент:\n\t{response_message}\n' \
            f'\tКод ответа:\n\t{response_code}\n' \
            f'\tОшибка:\n\t{ResponseCodeLenError}'
        client_logger.error(log_message)
        raise ResponseCodeLenError(response_code)
    if response_code not in RESPONSE_CODES:
        log_message = \
            f'\tФункция:\n\t{check_server_message.__name__}\n' \
            f'\tАргумент:\n\t{response_message}\n' \
            f'\tКод ответа:\n\t{response_code}\n' \
            f'\tОшибка:\n\t{ResponseCodeError}'
        client_logger.error(log_message)
        raise ResponseCodeError(response_code)
    log_message = \
        f'\tФункция:\n\t{check_server_message.__name__}\n' \
        f'\tАргумент:\n\t{response_message}\n' \
        f'\tОтвет:\n\t{response_message}'
    client_logger.info(log_message)
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

