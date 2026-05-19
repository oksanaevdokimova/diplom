"""TCP-транспорт (Wi‑Fi и GSM в режиме tcp)"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import socket # Модуль для работы с сокетами
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import QMutexLocker # Мьютекс для синхронизации доступа к данным
from transport._workers import SocketReader, TcpConnectWorker # Фоновые потоки для подключения и чтения из сокета
from core import diagnostic_messages as diag_msg
from transport.base import BaseTransport # Базовый класс транспорта

"""TCP-транспорт"""
class TcpTransport(BaseTransport):
    """Инициализация TCP-транспорта"""
    def __init__(
        self,
        host: str,
        port: int,
        connect_timeout: float = 60.0,
        channel_label: str = "TCP",
        parent: Any = None,
    ) -> None:
        super().__init__(parent) # Вызов конструктора родительского класса
        self._host = host # Хост
        self._port = port # Порт
        self._connect_timeout = connect_timeout
        self._channel_label = channel_label
        self._socket: socket.socket | None = None # Сокет
        self._reader: SocketReader | None = None # Читатель
        self._connect_worker: TcpConnectWorker | None = None # Поток подключения

    """Подключение к серверу"""
    def connect(self) -> None:
        if self.is_connected: # Если уже подключено, то ничего не делаем
            return
        if self._connect_worker is not None and self._connect_worker.isRunning(): # Если поток подключения уже запущен, то ничего не делаем
            return
        self._connect_worker = TcpConnectWorker(
            self._host, self._port, self._connect_timeout, self,
        )
        self._connect_worker.succeeded.connect(self._on_connect_succeeded) # Сигнал успешного подключения
        self._connect_worker.failed.connect(self._on_connect_failed) # Сигнал ошибки подключения
        self._connect_worker.finished.connect(self._clear_connect_worker) # Сигнал завершения подключения
        self._connect_worker.start() # Запускаем поток подключения

    """Отключение от сервера"""
    def disconnect(self) -> None:
        was_connected = self.is_connected # Флаг подключения
        self._stop_reader() # Останавливаем читатель
        self._close_socket() # Закрываем сокет
        self._set_connected(False) # Устанавливаем флаг подключения
        if was_connected: # Если было подключение, то вызываем сигнал отключения
            self.disconnected.emit() # Сигнал отключения

    """Отправка данных"""
    def send(self, data: bytes) -> None:
        if not self.is_connected or self._socket is None: # Если нет активного TCP-соединения, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_not_connected("TcpTransport"))
            return
        try: # Пытаемся отправить данные
            with QMutexLocker(self._mutex): # Блокировка мьютекса для синхронизации доступа к данным
                self._socket.sendall(data) # Отправляем данные
        except OSError as exc: # Если ошибка, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_io_error("TcpTransport", str(exc)))
            self.disconnect() # Отключаемся

    """Обработка успешного подключения"""
    def _on_connect_succeeded(self, sock: object) -> None:
        if not isinstance(sock, socket.socket): # Если неверный тип сокета, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_invalid_socket("TcpTransport"))
            return
        self._socket = sock # Сохраняем сокет
        self._reader = SocketReader(sock, self) # Создаем читатель
        self._reader.data_received.connect(self.data_received.emit) # Сигнал приема данных
        self._reader.disconnected.connect(self._on_peer_closed) # Сигнал отключения
        self._reader.read_error.connect(self._on_read_error) # Сигнал ошибки чтения
        self._reader.start() # Запускаем читатель
        self._set_connected(True) # Устанавливаем флаг подключения
        self.connected.emit() # Сигнал подключения

    """Обработка ошибки подключения"""
    def _on_connect_failed(self, message: str) -> None:
        self.error.emit(
            diag_msg.transport_tcp_connect_error(
                channel=self._channel_label,
                host=self._host,
                port=self._port,
                raw_detail=message,
                timeout_seconds=self._connect_timeout,
            ),
        )

    """Обработка закрытия соединения"""
    def _on_peer_closed(self) -> None:
        self.disconnect() # Отключаемся

    """Обработка ошибки чтения"""
    def _on_read_error(self, message: str) -> None:
        self.error.emit(diag_msg.transport_io_error("TcpTransport", message))
        self.disconnect() # Отключаемся

    """Остановка читателя"""
    def _stop_reader(self) -> None:
        if self._reader is None: # Если читатель не создан, то ничего не делаем
            return
        self._reader.stop() # Останавливаем читатель
        self._reader.wait(3000) # Ожидаем завершения читателя
        self._reader = None # Устанавливаем читатель в None

    """Закрытие сокета"""
    def _close_socket(self) -> None:
        if self._socket is None: # Если сокет не создан, то ничего не делаем
            return
        try: # Пытаемся закрыть сокет
            self._socket.shutdown(socket.SHUT_RDWR) # Закрываем сокет
        except OSError: # Если ошибка, то ничего не делаем
            pass
        try: # Пытаемся закрыть сокет
            self._socket.close() # Закрываем сокет
        except OSError: # Если ошибка, то ничего не делаем
            pass
        self._socket = None # Устанавливаем сокет в None

    """Очистка потока подключения"""
    def _clear_connect_worker(self) -> None:
        self._connect_worker = None # Устанавливаем поток подключения в None
