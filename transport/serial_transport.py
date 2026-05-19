"""USB-COM-транспорт через pyserial"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import QMutexLocker, QThread, Signal # Мьютекс для синхронизации доступа к данным, поток, сигналы
from core import diagnostic_messages as diag_msg
from transport.base import BaseTransport
try: # Пытаемся импортировать модуль pyserial
    import serial
except ImportError: # Если ошибка, то ничего не делаем
    serial = None # Устанавливаем serial в None

"""Поток подключения"""
class _SerialConnectWorker(QThread):
    succeeded = Signal(object) # Сигнал успешного подключения
    failed = Signal(str) # Сигнал ошибки подключения

    """Подключение к порту"""
    def __init__(self, port: str, baudrate: int, parent: Any = None) -> None:
        super().__init__(parent)
        self._port = port
        self._baudrate = baudrate

    """Запуск потока"""
    def run(self) -> None:
        if serial is None: # Если модуль pyserial не установлен, то вызываем сигнал ошибки подключения
            self.failed.emit(diag_msg.transport_module_missing("pyserial", "SerialTransport"))
            return
        try: # Пытаемся подключиться к порту
            handle = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=1.0,
            )
        except serial.SerialException as exc: # Если ошибка, то вызываем сигнал ошибки подключения
            self.failed.emit(diag_msg.transport_io_error("SerialTransport", str(exc)))
            return
        self.succeeded.emit(handle) # Сигнал успешного подключения

"""Поток чтения"""
class _SerialReader(QThread):
    data_received = Signal(bytes) # Сигнал приема данных
    disconnected = Signal() # Сигнал отключения
    read_error = Signal(str) # Сигнал ошибки чтения

    """Подключение к порту"""
    def __init__(self, handle: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self._handle = handle # Дескриптор порта
        self._running = True # Флаг работы

    """Остановка потока"""
    def stop(self) -> None:
        self._running = False # Устанавливаем флаг работы в False

    """Запуск потока"""
    def run(self) -> None:
        while self._running: # Пока поток работает
            try:
                if not self._handle.is_open: # Если порт не открыт, то вызываем сигнал отключения
                    self.disconnected.emit() # Сигнал отключения
                    break
                chunk = self._handle.read(4096) # Читаем данные из порта
            except Exception as exc:  # serial может бросать разные типы
                if self._running: # Если поток работает, то вызываем сигнал ошибки чтения
                    self.read_error.emit(str(exc)) # Сигнал ошибки чтения
                break
            if not chunk: # Если данные не получены, то пропускаем
                continue
            self.data_received.emit(bytes(chunk)) # Сигнал приема данных

"""USB-COM-транспорт"""
class SerialTransport(BaseTransport):
    """Инициализация USB-COM-транспорта"""
    def __init__(self, port: str, baudrate: int, parent: Any = None) -> None:
        super().__init__(parent) # Вызов конструктора родительского класса
        self._port = port # Порт
        self._baudrate = baudrate # Скорость передачи данных
        self._serial: Any = None # Дескриптор порта
        self._reader: _SerialReader | None = None # Поток чтения
        self._connect_worker: _SerialConnectWorker | None = None # Поток подключения

    """Подключение к порту"""
    def connect(self) -> None:
        if serial is None: # Если модуль pyserial не установлен, то вызываем сигнал ошибки подключения
            self.error.emit(diag_msg.transport_module_missing("pyserial", "SerialTransport"))
            return
        if self.is_connected: # Если уже подключено, то ничего не делаем
            return
        if self._connect_worker is not None and self._connect_worker.isRunning(): # Если поток подключения уже запущен, то ничего не делаем
            return
        self._connect_worker = _SerialConnectWorker(self._port, self._baudrate, self) # Создаем поток подключения
        self._connect_worker.succeeded.connect(self._on_connect_succeeded) # Сигнал успешного подключения
        self._connect_worker.failed.connect(self._on_connect_failed) # Сигнал ошибки подключения
        self._connect_worker.finished.connect(self._clear_connect_worker) # Сигнал завершения подключения
        self._connect_worker.start() # Запускаем поток подключения

    """Отключение от порта"""
    def disconnect(self) -> None:
        was_connected = self.is_connected # Флаг подключения
        self._stop_reader() # Останавливаем поток чтения
        self._close_serial() # Закрываем порт
        self._set_connected(False) # Устанавливаем флаг подключения в False
        if was_connected: # Если было подключение, то вызываем сигнал отключения
            self.disconnected.emit() # Сигнал отключения

    """Отправка данных"""
    def send(self, data: bytes) -> None:
        if not self.is_connected or self._serial is None: # Если нет активного COM-соединения, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_not_connected("SerialTransport"))
            return
        try: # Пытаемся отправить данные
            with QMutexLocker(self._mutex):
                self._serial.write(data) # Отправляем данные
                self._serial.flush() # Очищаем буфер
        except Exception as exc: # Если ошибка, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_io_error("SerialTransport", str(exc)))
            self.disconnect() # Отключаемся

    """Обработка успешного подключения"""
    def _on_connect_succeeded(self, handle: object) -> None:
        self._serial = handle # Сохраняем дескриптор порта
        self._reader = _SerialReader(handle, self) # Создаем поток чтения
        self._reader.data_received.connect(self.data_received.emit) # Сигнал приема данных
        self._reader.disconnected.connect(self._on_peer_closed) # Сигнал отключения
        self._reader.read_error.connect(self._on_read_error) # Сигнал ошибки чтения
        self._reader.start() # Запускаем поток чтения
        self._set_connected(True) # Устанавливаем флаг подключения
        self.connected.emit()

    """Обработка ошибки подключения"""
    def _on_connect_failed(self, message: str) -> None:
        self.error.emit(message)

    """Обработка закрытия соединения"""
    def _on_peer_closed(self) -> None:
        self.disconnect()

    """Ошибка чтения потока"""
    def _on_read_error(self, message: str) -> None:
        self.error.emit(message)
        self.disconnect()

    """Остановка потока чтения"""
    def _stop_reader(self) -> None:
        if self._reader is None: # Если поток чтения не создан, то ничего не делаем
            return
        self._reader.stop() # Останавливаем поток чтения
        self._reader.wait(3000) # Ожидаем завершения потока чтения
        self._reader = None # Устанавливаем поток чтения в None

    """Закрытие порта"""
    def _close_serial(self) -> None:
        if self._serial is None: # Если порт не создан, то ничего не делаем
            return
        try:
            if self._serial.is_open: # Если порт открыт, то закрываем его
                self._serial.close()
        except Exception: # Если ошибка, то ничего не делаем
            pass
        self._serial = None # Устанавливаем порт в None

    """Очистка потока подключения"""
    def _clear_connect_worker(self) -> None:
        self._connect_worker = None # Устанавливаем поток подключения в None
