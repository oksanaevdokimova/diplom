"""Модель прикладного сообщения: конверт + payload по типу.

Конверт (корень JSON):
  message_type, message_id, timestamp, actuator_id?, command_id?, payload

В payload — все поля, зависящие от типа (см. protocol/types.py и validate_message).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from protocol.types import (
    Action,
    Direction,
    Level,
    MessageType,
    ServiceType,
    State,
    Status,
)

@dataclass
class AppMessage:
    """Прикладное сообщение: общий конверт и словарь payload по message_type."""

    message_type: MessageType
    message_id: int | None = None
    timestamp: str | None = None
    actuator_id: int | None = None
    command_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> Status | None:
        if self.message_type is not MessageType.RESPONSE:
            return None
        raw = self.payload.get("status")
        return Status(str(raw)) if raw is not None else None

    @property
    def error_code(self) -> int | None:
        raw = self.payload.get("error_code")
        if raw is None:
            return None
        return int(raw)

    @property
    def text(self) -> str | None:
        raw = self.payload.get("text")
        if raw is not None:
            return str(raw)
        legacy = self.payload.get("description")
        return str(legacy) if legacy is not None else None

    @property
    def description(self) -> str | None:
        """Синоним text (совместимость с прежним API)."""
        return self.text

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"message_type": self.message_type.value, "payload": dict(self.payload)}
        if self.actuator_id is not None:
            data["actuator_id"] = self.actuator_id
        if self.command_id is not None:
            data["command_id"] = self.command_id
        if self.message_id is not None:
            data["message_id"] = self.message_id
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppMessage:
        raw_type = data.get("message_type")
        if raw_type is None:
            raise ValueError("В сообщении отсутствует поле message_type (тип сообщения)")
        message_type = MessageType(str(raw_type))

        payload_raw = data.get("payload")
        if payload_raw is None:
            payload: dict[str, Any] = {}
        elif not isinstance(payload_raw, dict):
            raise ValueError("Поле payload должно быть объектом (словарь)")
        else:
            payload = dict(payload_raw)

        _merge_legacy_root_fields(payload, data)

        return cls(
            message_type=message_type,
            message_id=_optional_id(data.get("message_id"), field="message_id"),
            timestamp=_optional_str(data.get("timestamp")),
            actuator_id=_optional_id(data.get("actuator_id"), field="actuator_id"),
            command_id=_optional_id(data.get("command_id"), field="command_id"),
            payload=payload,
        )


def _merge_legacy_root_fields(payload: dict[str, Any], data: dict[str, Any]) -> None:
    """Поддержка старого формата: status / error_code / description на корне JSON."""
    if "status" in data and "status" not in payload:
        payload["status"] = data["status"]
    if "error_code" in data and "error_code" not in payload:
        payload["error_code"] = data["error_code"]
    if "text" in data and "text" not in payload:
        payload["text"] = data["text"]
    if "description" in data and "text" not in payload and "description" not in payload:
        payload["text"] = data["description"]
    if "description" in payload and "text" not in payload:
        payload["text"] = payload.pop("description")


_id_counter = 0


def alloc_id() -> int:
    global _id_counter
    value = _id_counter
    _id_counter += 1
    return value


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_ping() -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE,
        message_id=alloc_id(),
        timestamp=utc_timestamp(),
        payload={"service_type": ServiceType.PING.value},
    )


def make_get_actuators() -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE,
        message_id=alloc_id(),
        timestamp=utc_timestamp(),
        command_id=alloc_id(),
        payload={"service_type": ServiceType.GET_ACTUATORS.value},
    )


_MOTION_PARAM_KEYS = ("position", "speed", "direction")


def _apply_motion_params(
    body: dict[str, Any],
    *,
    position: int | float | None = None,
    speed: int | float | None = None,
    direction: Direction | None = None,
) -> None:
    if position is not None:
        body["position"] = position
    if speed is not None:
        body["speed"] = speed
    if direction is not None:
        body["direction"] = direction.value


def make_command(
    *,
    action: Action,
    actuator_id: int | None = None,
    position: int | float | None = None,
    speed: int | float | None = None,
    direction: Direction | None = None,
) -> AppMessage:
    body: dict[str, Any] = {"action": action.value}
    _apply_motion_params(body, position=position, speed=speed, direction=direction)
    return AppMessage(
        message_type=MessageType.COMMAND,
        message_id=alloc_id(),
        timestamp=utc_timestamp(),
        actuator_id=actuator_id,
        command_id=alloc_id(),
        payload=body,
    )


def validate_message(message: AppMessage) -> None:
    payload = message.payload
    if message.message_type is MessageType.COMMAND:
        action_raw = payload.get("action")
        if action_raw is None:
            raise ValueError("Для command в payload обязательно поле action")
        try:
            Action(str(action_raw))
        except ValueError as exc:
            raise ValueError(f"Недопустимое значение action: {action_raw!r}") from exc
        _validate_id(message.actuator_id, "actuator_id", required=False)
        _validate_motion_params_optional(payload)
        return

    if message.message_type is MessageType.RESPONSE:
        if payload.get("status") is None:
            raise ValueError("Для response в payload обязательно поле status")
        try:
            Status(str(payload["status"]))
        except ValueError as exc:
            raise ValueError(f"Недопустимое значение status: {payload['status']!r}") from exc
        _validate_id(message.command_id, "command_id", required=False)
        _validate_id(message.actuator_id, "actuator_id", required=False)
        _validate_error_code(payload.get("error_code"))
        return

    if message.message_type is MessageType.TELEMETRY:
        if payload.get("state") is None:
            raise ValueError("Для telemetry в payload обязательно поле state")
        try:
            State(str(payload["state"]))
        except ValueError as exc:
            raise ValueError(f"Недопустимое значение state: {payload['state']!r}") from exc
        _validate_id(message.actuator_id, "actuator_id", required=False)
        _validate_motion_params_optional(payload)
        return

    if message.message_type is MessageType.DIAGNOSTIC:
        level_raw = payload.get("level")
        if level_raw is None:
            raise ValueError("Для diagnostic в payload обязательно поле level")
        try:
            Level(str(level_raw))
        except ValueError as exc:
            raise ValueError(f"Недопустимое значение level: {level_raw!r}") from exc
        _validate_error_code(payload.get("error_code"))
        return

    if message.message_type is MessageType.SERVICE:
        service_raw = payload.get("service_type")
        if service_raw is None:
            raise ValueError("Для service в payload обязательно поле service_type")
        try:
            service_type = ServiceType(str(service_raw))
        except ValueError as exc:
            raise ValueError(f"Недопустимое значение service_type: {service_raw!r}") from exc
        if service_type is ServiceType.GET_ACTUATORS:
            if message.actuator_id is not None:
                raise ValueError("Для get_actuators поле actuator_id не задаётся")
        elif service_type is ServiceType.ACTUATORS_LIST:
            if message.actuator_id is not None:
                raise ValueError("Для actuators_list поле actuator_id не задаётся")
            _validate_actuators_array(payload.get("actuators"))
        return

    raise ValueError(f"Неизвестный message_type: {message.message_type!r}")


def _validate_motion_params_optional(payload: dict[str, Any]) -> None:
    if "position" in payload:
        _validate_motion_number(payload["position"], "position")
    if "speed" in payload:
        _validate_motion_number(payload["speed"], "speed")
    if "direction" in payload:
        raw = payload["direction"]
        if raw is None:
            raise ValueError("Поле direction не может быть null")
        try:
            Direction(str(raw))
        except ValueError as exc:
            raise ValueError(
                "direction должен быть forward (вперёд) или backward (назад)"
            ) from exc


def _validate_motion_number(value: Any, field: str) -> None:
    if value is None:
        raise ValueError(f"Поле {field} не может быть null")
    if isinstance(value, bool):
        raise ValueError(f"{field} должно быть числом")
    if isinstance(value, (int, float)):
        return
    if isinstance(value, str):
        try:
            float(value)
        except ValueError as exc:
            raise ValueError(f"{field} должно быть числом: {value!r}") from exc
        return
    raise ValueError(f"{field} должно быть числом: {value!r}")


def _optional_error_code(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("error_code не может быть логическим значением")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("error_code не может быть пустым")
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError(f"error_code должен быть целым числом: {value!r}") from exc
    raise ValueError(f"error_code должен быть целым числом: {value!r}")


def _validate_error_code(value: Any) -> None:
    if value is None:
        return
    _optional_error_code(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_id(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} не может быть логическим значением")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field} не может быть отрицательным")
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValueError(f"{field} должен быть целым числом >= 0: {value!r}")


def _validate_id(value: int | None, field: str, *, required: bool) -> None:
    if value is None:
        if required:
            raise ValueError(f"Обязательно поле {field}")
        return
    if value < 0:
        raise ValueError(f"{field} не может быть отрицательным")


def _validate_actuators_array(actuators: Any) -> None:
    if not isinstance(actuators, list):
        raise ValueError("Для actuators_list обязателен массив actuators")
    for index, item in enumerate(actuators):
        if isinstance(item, str):
            if not item.strip():
                raise ValueError(f"actuators[{index}]: имя не может быть пустым")
            continue
        if isinstance(item, dict):
            raw_name = item.get("name")
            if raw_name is None or not str(raw_name).strip():
                raise ValueError(f"actuators[{index}]: обязательно непустое поле name")
            if "id" in item:
                _optional_id(item["id"], field=f"actuators[{index}].id")
            continue
        raise ValueError(f"actuators[{index}] должен быть строкой (имя) или объектом с полем name")
