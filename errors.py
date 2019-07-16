"""
Возможные ошибки и собственные исключения
"""
from jim.config import MAX_USERNAME_LEN, RESPONSE_CODE_LEN


class UsernameTooLongError(Exception):
    """
    Исключение.
    Имя пользователя слишком длинное
    """

    def __init__(self, username):
        """
        Конструктор класса
        :param username: str (Имя пользователя)
        """
        self.username = username

    def __str__(self):
        """
        Строковое представление класса
        :return: str (Сообщение об ошибке)
        """
        return f'Ошибка! Имя пользователя превышает {MAX_USERNAME_LEN} символов.'


class ResponseCodeError(Exception):
    """
    Исключение.
    Отсутствие переданного кода в протоколе
    """

    def __init__(self, code):
        """
        Конструктор класса
        :param code: int (Код ответа)
        """
        self.code = code

    def __str__(self):
        """
        Строковое представление класса
        :return: str (Сообщение об ошибке)
        """
        return f'Ошибка! Неверный код ответа: ({self.code})'


class ResponseCodeLenError(Exception):
    """
    Исключение.
    Несоответствие длины кода по протоколу
    """

    def __init__(self, code):
        """
        Конструктор класса
        :param code: int (Код ответа)
        """
        self.code = code

    def __str__(self):
        """
        Строковое представление класса
        :return: str (Сообщение об ошибке)
        """
        return f'Ошибка! Неверная длина кода ответа: ({self.code})\n' \
            f'Длина кода должна быть {RESPONSE_CODE_LEN} символа.'


class MissingKeyError(Exception):
    """
    Исключение.
    Отсутствие обязательного аргумента response
    """

    def __init__(self, key):
        """
        Конструктор класса
        :param key: str (Ключ)
        """
        self.key = key

    def __str__(self):
        """
        Строковое представление класса
        :return: str (Сообщение об ошибке)
        """
        return f'Отсутствует обязательный атрибут "{self.key}"'
