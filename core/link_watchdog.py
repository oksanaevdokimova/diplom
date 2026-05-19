"""Контроль связи по ping/pong с таймаутом"""

from __future__ import annotations
from collections.abc import Callable
from PySide6.QtCore import QObject, QTimer, Signal
from core import diagnostic_messages as diag_msg
from protocol.framing import serialize_line
from protocol.message import AppMessage, make_ping
from protocol.types import MessageType, ServiceType


class LinkWatchdog(QObject):
    """Контроль живости канала через пару ping/pong с таймаутом"""
    link_confirmed = Signal()
    link_lost = Signal(str)

    """Конструктор наблюдателя связи"""
    def __init__(self, timeout_seconds: float, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timeout_ms = max(1, int(timeout_seconds * 1000))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._send: Callable[[bytes], None] | None = None
        self._pending_ping_id: int | None = None
        self._check_reason = ""

    """Установить обработчик отправки байт (транспорт)"""
    def set_send_handler(self, handler: Callable[[bytes], None]) -> None:
        self._send = handler

    """Изменить интервал ожидания pong"""
    def set_timeout_seconds(self, timeout_seconds: float) -> None:
        self._timeout_ms = max(1, int(timeout_seconds * 1000))

    """Отправить ping и запустить таймер (reason — текст для сообщения об ошибке)"""
    def start_check(self, reason: str = "") -> None:
        self.cancel()
        self._check_reason = reason.strip()
        if self._send is None:
            self.link_lost.emit(diag_msg.link_send_unavailable())
            return
        ping = make_ping()
        self._pending_ping_id = ping.message_id
        self._send(serialize_line(ping))
        self._timer.start(self._timeout_ms)

    """Остановить ожидание pong"""
    def cancel(self) -> None:
        self._timer.stop()
        self._pending_ping_id = None
        self._check_reason = ""

    """Передать входящее сообщение; True если это ожидаемый pong"""
    def notify_message(self, message: AppMessage) -> bool:
        if not self._matches_pending_pong(message):
            return False
        self._timer.stop()
        self._pending_ping_id = None
        self._check_reason = ""
        self.link_confirmed.emit()
        return True

    """Проверка: сервис pong с command_id равным нашему ping message_id"""
    def _matches_pending_pong(self, message: AppMessage) -> bool:
        if self._pending_ping_id is None:
            return False
        if message.message_type is not MessageType.SERVICE:
            return False
        payload = message.payload or {}
        if payload.get("service_type") != ServiceType.PONG.value:
            return False
        return message.command_id == self._pending_ping_id

    """Истечение таймаут ожидания pong"""
    def _on_timeout(self) -> None:
        self._pending_ping_id = None
        self.link_lost.emit(
            diag_msg.link_lost(
                check=self._check_reason,
                detail=f"no pong within timeout, elapsed_limit_ms={self._timeout_ms}",
            ),
        )
