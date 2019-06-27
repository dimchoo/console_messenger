import sys
import re
from socket import socket, AF_INET, SOCK_STREAM
from jim.config import *
from jim.utils import send_message, get_message


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


if __name__ == '__main__':
    server = socket(AF_INET, SOCK_STREAM)
    try:
        addr = sys.argv[1]
    except IndexError:
        addr = DEFAULT_BIND_IP
    try:
        port = int(sys.argv[2])
    except IndexError:
        port = DEFAULT_SERVER_PORT
    except ValueError:
        print('Порт должен быть целым числом')
        sys.exit(0)

    server.bind((addr, port))
    server.listen(5)
    while True:
        client, addr = server.accept()
        presence = get_message(client)
        print(presence)
        response = presence_message_response(presence)
        send_message(client, response)
        client.close()
