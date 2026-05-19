"""Форматирование и проверка телеметрии для панели оператора"""

from __future__ import annotations

from dataclasses import dataclass

from protocol.message import AppMessage
from protocol.types import Action, Direction, State

_STATE_LABELS = {
    State.READY: "Готов",
    State.MOVING: "Движение",
    State.STOPPED: "Остановлен",
}

_DIRECTION_LABELS = {
    Direction.FORWARD: "Вперёд",
    Direction.BACKWARD: "Назад",
}

_ACTION_LABELS = {
    Action.MOVE: "Перемещение",
    Action.STOP: "Остановка",
}

TELEMETRY_ROW_DEFS: tuple[tuple[str, str], ...] = (
    ("mechanism", "Механизм:"),
    ("action", "Действие:"),
    ("direction", "Направление:"),
    ("position", "Положение:"),
    ("speed", "Скорость:"),
    ("state", "Состояние:"),
)


@dataclass(frozen=True)
class TelemetryRow:
    """Строка подробной телеметрии на панели"""
    key: str
    label: str
    value: str


def format_mechanism_display(actuator_id: int | None, name: str | None = None) -> str:
    """Механизм с ID в одной строке, как в списке и панели управления."""
    if actuator_id is None:
        return ""
    label = (name or "").strip()
    if label.startswith(f"ID: {actuator_id}"):
        return label
    if label:
        return f"ID: {actuator_id} {label}"
    return f"ID: {actuator_id}"


def validate_telemetry_message(message: AppMessage) -> list[str]:
    """Предупреждения о неполной или некорректной телеметрии"""
    issues: list[str] = []
    if message.actuator_id is None:
        issues.append("Нет actuator_id — нельзя привязать к механизму")
    payload = message.payload
    if not payload:
        issues.append("Пустой payload")
        return issues
    if payload.get("state") is None:
        issues.append("Нет поля state")
    else:
        try:
            State(str(payload["state"]))
        except ValueError:
            issues.append(f"Недопустимый state: {payload.get('state')!r}")
    return issues


def build_telemetry_rows(
    message: AppMessage | None,
    *,
    mechanism_name: str,
    actuator_id: int | None,
    default_speed: int | None = None,
) -> list[TelemetryRow]:
    """Строки панели телеметрии (всегда один и тот же набор полей)."""
    mechanism_label = format_mechanism_display(actuator_id, mechanism_name or None)
    action_text = ""
    direction_text = ""
    position_text = ""
    speed_text = ""
    state_text = ""

    if message is not None:
        payload = message.payload or {}
        display_id = message.actuator_id if message.actuator_id is not None else actuator_id
        mechanism_label = format_mechanism_display(display_id, mechanism_name or None)
        state_raw = payload.get("state")
        action_text = _format_action(payload.get("action"), state_raw)
        state_text = _format_state(state_raw)
        direction_text = _format_direction(payload.get("direction"))
        position_text = _format_number(payload.get("position"))
        speed_text = _format_number(payload.get("speed"))
        if not speed_text and default_speed is not None:
            try:
                state_enum = State(str(state_raw)) if state_raw is not None else None
            except ValueError:
                state_enum = None
            if state_enum in (State.MOVING, State.STOPPED):
                speed_text = str(default_speed)

    values = {
        "mechanism": mechanism_label,
        "action": action_text,
        "direction": direction_text,
        "position": position_text,
        "speed": speed_text,
        "state": state_text,
    }
    return [
        TelemetryRow(key, label, values[key])
        for key, label in TELEMETRY_ROW_DEFS
    ]


def _format_number(value: object) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _format_action(action: object, state: object) -> str:
    if action is not None:
        try:
            return _ACTION_LABELS[Action(str(action))]
        except ValueError:
            return str(action)
    if state is None:
        return ""
    try:
        state_enum = State(str(state))
    except ValueError:
        return ""
    if state_enum == State.MOVING:
        return _ACTION_LABELS[Action.MOVE]
    if state_enum == State.STOPPED:
        return _ACTION_LABELS[Action.STOP]
    return ""


def _format_direction(value: object) -> str:
    if value is None:
        return ""
    try:
        return _DIRECTION_LABELS[Direction(str(value))]
    except ValueError:
        return str(value)


def _format_state(value: object) -> str:
    if value is None:
        return ""
    try:
        return _STATE_LABELS[State(str(value))]
    except ValueError:
        return str(value)
