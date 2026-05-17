"""Базовый интерфейс транспорта: подключение и обмен байтами"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from abc import abstractmethod # Абстрактный базовый класс для создания интерфейсов
from PySide6.QtCore import QObject, QMutex, QMutexLocker, Signal # Базовый класс объектов Qt, мьютекс для синхронизации доступа к данным, сигналы для взаимодействия между потоками

"""Базовый класс транспорта"""
class BaseTransport(QObject):
    data_received = Signal(bytes) # Сигнал приема данных
    connected = Signal() # Сигнал подключения
    disconnected = Signal() # Сигнал отключения
    error = Signal(str) # Сигнал ошибки

    """Инициализация транспорта"""
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent) # Вызов конструктора родительского класса
        self._mutex = QMutex() # Мьютекс для синхронизации доступа к данным
        self._is_connected = False # Флаг подключения

    """Проверка подключения"""
    @property
    def is_connected(self) -> bool:
        return self._is_connected # Возвращение флага подключения

    """Подключение транспорта"""
    @abstractmethod
    def connect(self) -> None:
        pass

    """Отключение транспорта"""
    @abstractmethod
    def disconnect(self) -> None:
        pass

    """Отправка данных"""
    @abstractmethod
    def send(self, data: bytes) -> None:
        pass

    """Установка флага подключения"""
    def _set_connected(self, connected: bool) -> None:
        with QMutexLocker(self._mutex): # Блокировка мьютекса для синхронизации доступа к данным
            self._is_connected = connected # Установка флага подключения
