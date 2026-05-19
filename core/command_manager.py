"""Ожидание ответа response от контроллера по command_id отправленной команды"""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer, Signal

from core import diagnostic_messages as diag_msg
from protocol.message import AppMessage
from protocol.types import Action, Direction, Status

_DIRECTION_LABELS = {
    Direction.FORWARD.value: "вперёд",
    Direction.BACKWARD.value: "назад",
}


def response_status_label(status: Status) -> str:
    """Краткая русская метка для статуса ответа контроллера"""
    if status == Status.ACCEPTED:
        return "Принято"
    if status == Status.COMPLETED:
        return "Выполнено"
    if status == Status.REJECTED:
        return "Отклонено"
    if status == Status.ERROR:
        return "Ошибка"
    return status.value


def format_command_params(command: AppMessage) -> str:
    """Параметры команды для журнала через «; »."""
    payload = command.payload or {}
    parts: list[str] = []
    action = payload.get("action")
    if action == Action.STOP.value:
        parts.append("остановка")
    elif action == Action.MOVE.value:
        parts.append("перемещение")
        direction = payload.get("direction")
        if direction is not None:
            parts.append(
                f"направление {_DIRECTION_LABELS.get(str(direction), direction)}"
            )
        if "speed" in payload:
            parts.append(f"скорость {payload['speed']}")
        if "position" in payload:
            parts.append(f"положение {payload['position']}")
    elif action is not None:
        parts.append(str(action))
    return "; ".join(parts)


def format_command_journal_description(
    prefix: str, command: AppMessage, mechanism_label: str
) -> str:
    """Описание события журнала: префикс, механизм и параметры в скобках."""
    params = format_command_params(command)
    if params:
        return f"{prefix}, механизм {mechanism_label} ({params})"
    return f"{prefix}, механизм {mechanism_label}"


class CommandManager(QObject):
    """Ожидание ответа response по command_id отправленной команды"""
    command_accepted = Signal(AppMessage)
    command_rejected = Signal(AppMessage)
    command_error = Signal(AppMessage)
    response_timeout = Signal(str)
    orphan_response = Signal(AppMessage)

    """Конструктор менеджера команд"""
    def __init__(self, timeout_seconds: float, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timeout_ms = max(1, int(timeout_seconds * 1000))
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._pending_command_id: int | None = None

    """Обновить длительность ожидания ответа"""
    def set_timeout_seconds(self, timeout_seconds: float) -> None:
        self._timeout_ms = max(1, int(timeout_seconds * 1000))

    """Запомнить отправленную команду и запустить таймер"""
    def register_sent(self, command: AppMessage) -> None:
        if command.command_id is None:
            return
        self.clear()
        self._pending_command_id = command.command_id
        self._timer.start(self._timeout_ms)

    """Снять ожидание ответа"""
    def clear(self) -> None:
        self._timer.stop()
        self._pending_command_id = None

    """Разбор входящего response; выбор сигнала по статусу"""
    def handle_response(self, message: AppMessage) -> bool:
        if self._pending_command_id is None:
            self.orphan_response.emit(message)
            return False # Нечего сопоставлять с отправленной командой
        if message.command_id != self._pending_command_id:
            self.orphan_response.emit(message)
            return False # Ответ относится к другой команде
        self._timer.stop()
        self._pending_command_id = None
        status = message.status
        if status in (Status.ACCEPTED, Status.COMPLETED):
            self.command_accepted.emit(message)
            return True
        if status == Status.REJECTED:
            self.command_rejected.emit(message)
            return True
        if status == Status.ERROR:
            self.command_error.emit(message)
            return True
        self.command_error.emit(message) # Прочие статусы трактуем как ошибку ответа
        return True

    """Таймаут ожидания ответа контроллера"""
    def _on_timeout(self) -> None:
        if self._pending_command_id is None:
            return
        command_id = self._pending_command_id
        self._pending_command_id = None
        self.response_timeout.emit(
            diag_msg.command_response_timeout(command_id, self._timeout_ms),
        )
