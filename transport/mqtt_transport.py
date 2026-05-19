"""GSM MQTT-транспорт через paho-mqtt"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import socket
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import Q_ARG, QMetaObject, Qt, QThread, Signal, Slot
from core import diagnostic_messages as diag_msg
from transport.base import BaseTransport
try: # Пытаемся импортировать модуль paho-mqtt
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None  # type: ignore[assignment]

"""Поток подключения"""
class _MqttConnectWorker(QThread):
    succeeded = Signal(object) # Сигнал успешного подключения
    failed = Signal(str) # Сигнал ошибки подключения

    """Подключение к MQTT-брокеру"""
    def __init__(
        self,
        host: str,
        port: int,
        topic_messages: str,
        connect_timeout: float = 60.0,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._host = host
        self._port = port
        self._topic_messages = topic_messages
        self._connect_timeout = max(1.0, float(connect_timeout))

    """Запуск потока"""
    def run(self) -> None:
        if mqtt is None: # Если модуль paho-mqtt не установлен, то вызываем сигнал ошибки подключения
            self.failed.emit(diag_msg.transport_module_missing("paho-mqtt", "MqttTransport"))
            return
        keepalive = max(10, int(self._connect_timeout))
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        prev_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self._connect_timeout)
        try:
            client.connect(self._host, self._port, keepalive=keepalive)
            client.loop_start() # Запускаем цикл обработки событий MQTT
            result, _ = client.subscribe(self._topic_messages) # Подписываемся на топик сообщений
            if result != mqtt.MQTT_ERR_SUCCESS: # Если ошибка, то вызываем сигнал ошибки подключения
                client.loop_stop() # Останавливаем цикл обработки событий MQTT
                client.disconnect() # Отключаемся от MQTT-брокера
                self.failed.emit("subscribe to topic failed")
                return
        except Exception as exc: # Если ошибка, то вызываем сигнал ошибки подключения
            self.failed.emit(str(exc))
            return
        finally:
            socket.setdefaulttimeout(prev_timeout)
        self.succeeded.emit(client) # Сигнал успешного подключения

"""MQTT-транспорт"""
class MqttTransport(BaseTransport):
    """Инициализация MQTT-транспорта"""
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        topic_command: str,
        topic_messages: str,
        connect_timeout: float = 60.0,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._topic_command = topic_command
        self._topic_messages = topic_messages
        self._connect_timeout = connect_timeout
        self._client: Any = None
        self._connect_worker: _MqttConnectWorker | None = None

    """Подключение к MQTT-брокеру"""
    def connect(self) -> None:
        if mqtt is None: # Если модуль paho-mqtt не установлен, то вызываем сигнал ошибки подключения
            self.error.emit(diag_msg.transport_module_missing("paho-mqtt", "MqttTransport"))
            return
        if self.is_connected: # Если уже подключено, то ничего не делаем
            return
        if self._connect_worker is not None and self._connect_worker.isRunning(): # Если поток подключения уже запущен, то ничего не делаем
            return
        self._connect_worker = _MqttConnectWorker(
            self._broker_host,
            self._broker_port,
            self._topic_messages,
            self._connect_timeout,
            self,
        )
        self._connect_worker.succeeded.connect(self._on_connect_succeeded) # Сигнал успешного подключения
        self._connect_worker.failed.connect(self._on_connect_failed) # Сигнал ошибки подключения
        self._connect_worker.finished.connect(self._clear_connect_worker) # Сигнал завершения подключения
        self._connect_worker.start()

    """Отключение от MQTT-брокера"""
    def disconnect(self) -> None:
        was_connected = self.is_connected # Флаг подключения
        client = self._client
        self._client = None # Устанавливаем клиента в None
        self._set_connected(False) # Устанавливаем флаг подключения в False
        if client is not None: # Если клиент существует, то останавливаем цикл обработки событий MQTT и отключаемся от MQTT-брокера
            try:
                client.loop_stop() # Останавливаем цикл обработки событий MQTT
                client.disconnect() # Отключаемся от MQTT-брокера
            except Exception: # Если ошибка, то ничего не делаем
                pass
        if was_connected: # Если было подключение, то вызываем сигнал отключения
            self.disconnected.emit()

    """Отправка данных"""
    def send(self, data: bytes) -> None:
        if not self.is_connected or self._client is None: # Если нет активного MQTT-соединения, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_not_connected("MqttTransport"))
            return
        try: # Пытаемся отправить данные
            result = self._client.publish(self._topic_command, payload=data)
            if result.rc != 0: # Если ошибка, то вызываем сигнал ошибки
                self.error.emit(diag_msg.transport_mqtt_publish_failed(result.rc))
                self.disconnect() # Отключаемся
        except Exception as exc: # Если ошибка, то вызываем сигнал ошибки
            self.error.emit(diag_msg.transport_io_error("MqttTransport", str(exc)))
            self.disconnect() # Отключаемся

    """Обработка успешного подключения"""
    def _on_connect_succeeded(self, client: object) -> None:
        self._client = client # Сохраняем клиента
        self._client.on_message = self._on_message # Устанавливаем обработчик сообщений
        self._client.on_disconnect = self._on_disconnect # Устанавливаем обработчик отключения
        self._set_connected(True) # Устанавливаем флаг подключения в True
        self.connected.emit() # Сигнал подключения

    """Обработка ошибки подключения"""
    def _on_connect_failed(self, message: str) -> None:
        self.error.emit(
            diag_msg.transport_tcp_connect_error(
                channel="MQTT",
                host=self._broker_host,
                port=self._broker_port,
                raw_detail=message,
                timeout_seconds=self._connect_timeout,
            ),
        )

    @Slot(bytes)
    def _deliver_mqtt_payload(self, payload: bytes) -> None:
        self.data_received.emit(payload)

    """Обработка сообщений (callback paho — передача в поток Qt)"""
    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        payload = message.payload
        if isinstance(payload, bytes) and payload:
            QMetaObject.invokeMethod(
                self,
                "_deliver_mqtt_payload",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bytes, payload),
            )

    """Обработка отключения"""
    def _on_disconnect(self, client: Any, userdata: Any, disconnect_flags: Any, reason_code: Any, properties: Any = None) -> None:
        if self.is_connected: # Если подключено, то устанавливаем флаг подключения в False и вызываем сигнал отключения
            self._set_connected(False) # Устанавливаем флаг подключения в False
            self.disconnected.emit() # Сигнал отключения

    """Очистка потока подключения"""
    def _clear_connect_worker(self) -> None:
        self._connect_worker = None # Устанавливаем поток подключения в None
