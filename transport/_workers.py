"""Фоновые потоки для подключения и чтения из сокета"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import socket # Модуль для работы с сокетами
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import QThread, Signal # Поток, сигналы

"""Поток подключения"""
class TcpConnectWorker(QThread):
    succeeded = Signal(object) # Сигнал успешного подключения
    failed = Signal(str) # Сигнал ошибки подключения

    """Подключение к серверу"""
    def __init__(self, host: str, port: int, parent: Any = None) -> None:
        super().__init__(parent) # Вызов конструктора родительского класса
        self._host = host
        self._port = port

    """Запуск потока"""
    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создаем сокет
        try:
            sock.connect((self._host, self._port)) # Подключаемся к серверу
            sock.settimeout(1.0) # Устанавливаем таймаут
            self.succeeded.emit(sock) # Сигнал успешного подключения
        except OSError as exc: # Если ошибка, то вызываем сигнал ошибки подключения
            sock.close() # Закрываем сокет
            self.failed.emit(str(exc)) # Сигнал ошибки подключения

"""Чтение из сокета"""
class SocketReader(QThread):
    data_received = Signal(bytes) # Сигнал приема данных
    disconnected = Signal() # Сигнал отключения
    read_error = Signal(str) # Сигнал ошибки чтения

    """Инициализация потока чтения"""
    def __init__(self, sock: socket.socket, parent: Any = None) -> None:
        super().__init__(parent) # Вызов конструктора родительского класса
        self._sock = sock
        self._running = True

    """Остановка потока"""
    def stop(self) -> None:
        self._running = False # Устанавливаем флаг остановки в True

    """Запуск потока"""
    def run(self) -> None:
        while self._running: # Пока поток работает
            try:
                chunk = self._sock.recv(4096) # Читаем данные из сокета
            except socket.timeout: # Если таймаут, то пропускаем
                continue
            except OSError as exc: # Если ошибка, то вызываем сигнал ошибки чтения
                if self._running: # Если поток работает, то вызываем сигнал ошибки чтения
                    self.read_error.emit(str(exc))
                break
            if not chunk: # Если данные не получены, то вызываем сигнал отключения
                self.disconnected.emit() # Сигнал отключения
                break
            self.data_received.emit(chunk) # Сигнал приема данных
