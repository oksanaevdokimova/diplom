"""Разбор входящих байтов транспорта в AppMessage и маршрутизация по типу"""

from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal

from core import diagnostic_messages as diag_msg
from protocol.framing import LineFramer
from protocol.message import AppMessage, validate_message
from protocol.types import MessageType


class MessageProcessor(QObject):
    """Разбор входящего потока байт в сообщения и рассылка по типам"""
    response_received = Signal(AppMessage)
    telemetry_received = Signal(AppMessage)
    diagnostic_received = Signal(AppMessage)
    service_received = Signal(AppMessage)
    parse_error = Signal(str)
    valid_message_received = Signal(AppMessage)

    """Конструктор процессора сообщений"""
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._framer = LineFramer()

    """Сброс неполной строки в буфере"""
    def clear(self) -> None:
        self._framer.clear()

    """Приём порции байт из транспорта"""
    def feed_bytes(self, data: bytes) -> None:
        for line in self._framer.feed_bytes(data):
            self._process_line(line)

    """Разбор одной текстовой строки JSON"""
    def _process_line(self, line: str) -> None:
        try:
            message = self._parse_json_line(line)
        except ValueError as exc:
            self.parse_error.emit(diag_msg.protocol_validation_error(str(exc)))
            return
        if self._dispatch(message):
            self.valid_message_received.emit(message)

    """Преобразование строки в AppMessage с проверкой схемы"""
    def _parse_json_line(self, line: str) -> AppMessage:
        stripped = line.strip()
        if not stripped:
            raise ValueError(diag_msg.protocol_empty_line())
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(diag_msg.protocol_json_error(str(exc))) from exc
        if not isinstance(data, dict):
            raise ValueError(diag_msg.protocol_not_object())
        message = AppMessage.from_dict(data)
        validate_message(message)
        return message

    """Выбор целевого сигнала по message_type"""
    def _dispatch(self, message: AppMessage) -> bool:
        if message.message_type == MessageType.RESPONSE:
            self.response_received.emit(message)
            return True
        if message.message_type == MessageType.TELEMETRY:
            self.telemetry_received.emit(message)
            return True
        if message.message_type == MessageType.DIAGNOSTIC:
            self.diagnostic_received.emit(message)
            return True
        if message.message_type == MessageType.SERVICE:
            self.service_received.emit(message)
            return True
        if message.message_type == MessageType.COMMAND:
            self.parse_error.emit(diag_msg.protocol_unexpected_command())
            return False
        self.parse_error.emit(diag_msg.protocol_unknown_type(message.message_type.value))
        return False
