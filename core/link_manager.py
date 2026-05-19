"""Связь с контроллером: транспорт, разбор строк и контроль ping/pong."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from core import diagnostic_messages as diag_msg
from core.actuator_manager import ActuatorManager
from core.link_watchdog import LinkWatchdog
from core.message_processor import MessageProcessor
from protocol.framing import serialize_line
from protocol.message import AppMessage
from transport.base import BaseTransport
from transport.manager import create_transport


def format_channel_short(config: dict[str, Any]) -> str:
    """Краткое имя канала для панели «Состояние связи»"""
    transport = str(config.get("active_transport", "usb"))
    if transport == "usb":
        return "USB-COM"
    if transport == "wifi":
        return "Wi-Fi"
    if transport == "gsm":
        gsm = config.get("gsm", {})
        if str(gsm.get("mode", "mqtt")) == "tcp":
            return "GSM TCP"
        return "GSM MQTT"
    return transport


def format_connection_config(config: dict[str, Any]) -> str:
    """Параметры подключения для журнала: канал и адреса через «; »."""
    transport = str(config.get("active_transport", "usb"))
    parts: list[str] = [format_channel_short(config)]
    if transport == "usb":
        usb = config["usb"]
        parts.extend((f"порт {usb['port']}", f"{usb['baudrate']} бод"))
    elif transport == "wifi":
        wifi = config["wifi"]
        parts.extend((f"хост {wifi['host']}", f"порт {wifi['port']}"))
    elif transport == "gsm":
        gsm = config["gsm"]
        if str(gsm.get("mode", "mqtt")) == "tcp":
            parts.extend((f"хост {gsm['host']}", f"порт {gsm['port']}"))
        else:
            parts.append(f"брокер {gsm['broker_host']}:{gsm['broker_port']}")
            parts.append(f"топик команд {gsm['topic_command']}")
            parts.append(f"топик сообщений {gsm['topic_messages']}")
    return "; ".join(parts)


class LinkManager(QObject):
    """Управление транспортом, watchdog и разбором сообщений для UI"""
    link_ready = Signal()
    link_failed = Signal(str)
    command_link_ok = Signal()
    command_failed = Signal(str)
    transport_disconnected = Signal()
    actuators_loaded = Signal(list)
    actuators_failed = Signal(str)
    response_received = Signal(AppMessage)
    telemetry_received = Signal(AppMessage)
    diagnostic_received = Signal(AppMessage)
    parse_error = Signal(str)
    valid_message_received = Signal(AppMessage)

    """Конструктор менеджера связи"""
    def __init__(self, config: dict[str, Any], parent: QObject | None = None) -> None:
        super().__init__(parent)
        timeout = float(config.get("timeout_seconds", 60))
        self._connection_watchdog = LinkWatchdog(timeout, parent=self)
        self._connection_watchdog.set_send_handler(self._send_bytes)
        self._connection_watchdog.link_confirmed.connect(self._on_connection_confirmed)
        self._connection_watchdog.link_lost.connect(self._on_connection_lost)
        self._command_watchdog = LinkWatchdog(timeout, parent=self)
        self._command_watchdog.set_send_handler(self._send_bytes)
        self._command_watchdog.link_confirmed.connect(self._on_command_confirmed)
        self._command_watchdog.link_lost.connect(self._on_command_lost)
        self._actuators = ActuatorManager(timeout, parent=self)
        self._actuators.set_send_handler(self._send_bytes)
        self._actuators.actuators_loaded.connect(self.actuators_loaded.emit)
        self._actuators.actuators_failed.connect(self.actuators_failed.emit)
        self._processor = MessageProcessor(parent=self)
        self._processor.service_received.connect(self._on_service_message)
        self._processor.response_received.connect(self.response_received.emit)
        self._processor.telemetry_received.connect(self.telemetry_received.emit)
        self._processor.diagnostic_received.connect(self.diagnostic_received.emit)
        self._processor.parse_error.connect(self.parse_error.emit)
        self._processor.valid_message_received.connect(self.valid_message_received.emit)
        self._transport: BaseTransport | None = None
        self._awaiting_connect = False
        self._waiting_command = False

    @property
    def is_connected(self) -> bool:
        """Признак активного транспортного соединения"""

        return self._transport is not None and self._transport.is_connected

    """Создать транспорт по конфигурации и начать подключение"""
    def connect(self, config: dict[str, Any]) -> None:
        timeout = float(config.get("timeout_seconds", 60))
        self._connection_watchdog.set_timeout_seconds(timeout)
        self._command_watchdog.set_timeout_seconds(timeout)
        self._actuators.set_timeout_seconds(timeout)
        self.disconnect()
        self._processor.clear()
        self._awaiting_connect = True
        self._waiting_command = False
        transport = self._create_transport(config)
        self._transport = transport
        transport.connected.connect(self._on_transport_connected)
        transport.disconnected.connect(self._on_transport_disconnected)
        transport.error.connect(self._on_transport_error)
        transport.data_received.connect(self._on_data_received)
        transport.connect()

    """Закрыть транспорт и снять таймеры"""
    def disconnect(self) -> None:
        self._awaiting_connect = False
        self._waiting_command = False
        self._connection_watchdog.cancel()
        self._command_watchdog.cancel()
        self._actuators.clear()
        self._processor.clear()
        if self._transport is None:
            return
        transport = self._transport
        self._transport = None
        transport.disconnect()
        transport.deleteLater()

    """Отправка команды на контроллер"""
    def send_command(self, message: AppMessage) -> None:
        if self._transport is None or not self._transport.is_connected: # Если нет соединения, то выбрасываем ошибку
            self.link_failed.emit(diag_msg.link_command_not_connected())
            return
        self._waiting_command = True # Устанавливаем флаг ожидания команды
        self._transport.send(serialize_line(message)) # Отправляем команду на контроллер
        self._command_watchdog.start_check("Отправка команды") # Запускаем таймер ожидания команды

    """Фабрика транспорта по активному каналу из конфигурации"""
    def _create_transport(self, config: dict[str, Any]) -> BaseTransport:
        return create_transport(config, parent=self)

    """Отправка произвольных байт (ping и др.) через активный транспорт"""
    def _send_bytes(self, data: bytes) -> None:
        if self._transport is None or not self._transport.is_connected:
            return
        self._transport.send(data)

    """Транспорт подключён — начать проверку связи ping/pong"""
    def _on_transport_connected(self) -> None:
        self._connection_watchdog.start_check("подключение")

    """Закрытие сокета/COM со стороны ОС или пользователя"""
    def _on_transport_disconnected(self) -> None:
        self._awaiting_connect = False
        self._waiting_command = False
        self._connection_watchdog.cancel()
        self._command_watchdog.cancel()
        self.transport_disconnected.emit()

    """Ошибка транспорта: до установления связи или при активном канале"""
    def _on_transport_error(self, message: str) -> None:
        if self.is_connected:
            self.link_failed.emit(message)
            return # Сообщить об ошибке без повторного disconnect-тректа
        self._fail_connect(message)

    """Проксирование входящих байт в построчный разбор JSON"""
    def _on_data_received(self, data: bytes) -> None:
        self._processor.feed_bytes(data)

    """Маршрутизация service-сообщений: actuators или ping/pong watchdog"""
    def _on_service_message(self, message: AppMessage) -> None:
        if self._actuators.try_handle_message(message):
            return
        self._connection_watchdog.notify_message(message)
        self._command_watchdog.notify_message(message)

    """Получен pong при ожидании после подключения"""
    def _on_connection_confirmed(self) -> None:
        if not self._awaiting_connect:
            return
        self._awaiting_connect = False
        self.link_ready.emit()
        self._actuators.request_actuators()

    """Нет pong в срок при установлении связи или позже"""
    def _on_connection_lost(self, message: str) -> None:
        was_connect = self._awaiting_connect
        self._awaiting_connect = False
        self._waiting_command = False
        self._command_watchdog.cancel()
        self.disconnect()
        self.link_failed.emit(message)
        self.transport_disconnected.emit()

    """Получен pong после отправки команды"""
    def _on_command_confirmed(self) -> None:
        if not self._waiting_command:
            return
        self._waiting_command = False
        self.command_link_ok.emit()

    """Нет pong после отправки команды"""
    def _on_command_lost(self, message: str) -> None:
        if not self._waiting_command:
            return
        self._waiting_command = False
        self.command_failed.emit(message)

    """Фиксация ошибки до перехода в состояние «связь установлена»"""
    def _fail_connect(self, message: str) -> None:
        self._awaiting_connect = False
        self._waiting_command = False
        self.disconnect()
        self.link_failed.emit(message)
        self.transport_disconnected.emit()
