"""Упаковка сообщений: один JSON-объект на строку"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import json # Модуль для работы с JSON
from protocol.message import AppMessage, validate_message # Импорт класса AppMessage и функции validate_message

"""Сериализация сообщения в UTF-8 байты с завершающим \\n"""
def serialize_line(message: AppMessage, *, validate: bool = True) -> bytes:
    if validate: # Если validate True, то проверяем сообщение
        validate_message(message)
    line = json.dumps(message.to_dict(), ensure_ascii=False, separators=(",", ":")) # Сериализация сообщения в JSON
    return (line + "\n").encode("utf-8") # Преобразование строки в байты с завершающим \\n

"""Разбирает одну JSON-строку (без \\n) в AppMessage"""
def parse_line(line: str, *, validate: bool = True) -> AppMessage:
    stripped = line.strip() # Удаление пробелов и символов новой строки
    if not stripped: # Если строка пустая, то выбрасываем ошибку
        raise ValueError("Пустая строка сообщения")
    data = json.loads(stripped) # Преобразование строки в словарь
    if not isinstance(data, dict): # Если данные не являются словарём, то выбрасываем ошибку
        raise ValueError("Сообщение должно быть JSON-объектом")
    message = AppMessage.from_dict(data) # Преобразование словаря в сообщение
    if validate: # Если validate True, то проверяем сообщение
        validate_message(message)
    return message # Возвращение сообщения

"""Класс для упаковки сообщений: один JSON-объект на строку"""
class LineFramer:
    """Инициализация буфера"""
    def __init__(self) -> None:
        self._buffer = bytearray() # Буфер для хранения входящих байт

    """Добавляет байты в буфер и возвращает полные строки (без \\n)"""
    def feed_bytes(self, data: bytes) -> list[str]:
        self._buffer.extend(data) # Добавление байт в буфер
        lines: list[str] = [] # Список для хранения полных строк (без \\n)
        while True:
            newline = self._buffer.find(b"\n") # Поиск символа новой строки
            if newline < 0: # Если символ новой строки не найден, то выходим из цикла
                break
            raw_line = bytes(self._buffer[:newline]) # Преобразование байт в строку
            del self._buffer[: newline + 1] # Удаление байт из буфера
            if not raw_line: # Если строка пустая, то пропускаем
                continue
            lines.append(raw_line.decode("utf-8")) # Добавление строки в список
        return lines # Возвращение списка строк

    """Удобная обёртка: байты → список AppMessage"""
    def feed_messages(self, data: bytes, *, validate: bool = True) -> list[AppMessage]:
        return [parse_line(line, validate=validate) for line in self.feed_bytes(data)] # Возвращение списка сообщений

    """Очистка буфера"""
    def clear(self) -> None:
        self._buffer.clear() # Очистка буфера
