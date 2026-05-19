"""Запрос списка механизмов у контроллера и разбор actuators_list"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from core import diagnostic_messages as diag_msg
from protocol.actuators import ActuatorRegistry
from protocol.framing import serialize_line
from protocol.message import AppMessage, make_get_actuators
from protocol.types import ServiceType


def entries_to_ui_list(entries: list) -> list[tuple[int, str]]:
    """Преобразование записей реестра в пары (id, имя) для списков Qt"""
    return [(entry.id, entry.name) for entry in entries]


class ActuatorManager(QObject):
    """Запрос actuators_list у контроллера и разбор ответа по command_id"""
    actuators_loaded = Signal(list)
    actuators_failed = Signal(str)

    """Конструктор менеджера списка механизмов"""
    def __init__(self, timeout_seconds: float, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timeout_ms = max(1, int(timeout_seconds * 1000))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._send: Callable[[bytes], None] | None = None
        self._registry = ActuatorRegistry()
        self._pending_command_id: int | None = None

    """Подключить функцию отправки сырых байт в транспорт"""
    def set_send_handler(self, handler: Callable[[bytes], None]) -> None:
        self._send = handler

    """Обновить длительность ожидания ответа actuators_list"""
    def set_timeout_seconds(self, timeout_seconds: float) -> None:
        self._timeout_ms = max(1, int(timeout_seconds * 1000))

    """Сброс реестра и отмена текущего запроса"""
    def clear(self) -> None:
        self._registry.clear()
        self.cancel_request()

    """Отправить get_actuators и запустить таймер ответа"""
    def request_actuators(self) -> None:
        self.cancel_request()
        if self._send is None:
            self.actuators_failed.emit(diag_msg.actuators_send_unavailable())
            return
        request = make_get_actuators()
        self._pending_command_id = request.command_id
        self._send(serialize_line(request))
        self._timer.start(self._timeout_ms)

    """Остановить ожидание ответа"""
    def cancel_request(self) -> None:
        self._timer.stop()
        self._pending_command_id = None

    """Обработать входящее сообщение; True если это наш ответ actuators_list"""
    def try_handle_message(self, message: AppMessage) -> bool:
        payload = message.payload or {}
        if payload.get("service_type") != ServiceType.ACTUATORS_LIST.value:
            return False
        if self._pending_command_id is None:
            return False
        if message.command_id != self._pending_command_id:
            return False
        self.cancel_request()
        try:
            entries = self._registry.load_from_controller_message(message)
        except ValueError as exc:
            self.actuators_failed.emit(diag_msg.actuators_list_invalid(str(exc)))
            return True
        self.actuators_loaded.emit(entries_to_ui_list(entries))
        return True

    """Истечение таймера ожидания actuators_list"""
    def _on_timeout(self) -> None:
        self._pending_command_id = None
        self.actuators_failed.emit(diag_msg.actuators_list_timeout())
