"""Модель прикладного сообщения и проверка обязательных полей по типу"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from dataclasses import dataclass # Класс для создания классов с автоматическим созданием методов
from datetime import datetime, timezone # Модуль для работы с датой и временем
from typing import Any # Универсальный тип для значений в словаре конфигурации
from protocol.types import ( # Импорт типов сообщений
    Action,
    Direction,
    Level,
    MessageType,
    ServiceType,
    State,
    Status,
)

"""Прикладное сообщение; не все поля используются для каждого message_type"""
@dataclass
class AppMessage:
    message_type: MessageType # Тип сообщения
    message_id: int | None = None # Идентификатор сообщения (0, 1, 2, …)
    timestamp: str | None = None # Время сообщения
    actuator_id: int | None = None # Идентификатор исполнительного механизма (0, 1, 2, …)
    command_id: int | None = None # Идентификатор команды (0, 1, 2, …)
    payload: dict[str, Any] | None = None # Содержимое сообщения в зависимости от типа сообщения
    status: Status | None = None # Статус сообщения
    error_code: str | None = None # Код ошибки
    description: str | None = None # Описание сообщения

    """Преобразование сообщения в словарь"""
    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"message_type": self.message_type.value} # Тип сообщения
        if self.message_id is not None:
            data["message_id"] = self.message_id # Идентификатор сообщения
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp # Время сообщения
        if self.actuator_id is not None:
            data["actuator_id"] = self.actuator_id # Идентификатор исполнительного механизма
        if self.command_id is not None:
            data["command_id"] = self.command_id # Идентификатор команды
        if self.payload is not None:
            data["payload"] = self.payload # Содержимое сообщения в зависимости от типа сообщения
        if self.status is not None:
            data["status"] = self.status.value # Статус сообщения
        if self.error_code is not None:
            data["error_code"] = self.error_code # Код ошибки
        if self.description is not None:
            data["description"] = self.description # Описание сообщения
        return data

    """Преобразование словаря в сообщение"""
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppMessage:
        raw_type = data.get("message_type") # Тип сообщения
        if raw_type is None: # Если тип сообщения отсутствует, то выбрасываем ошибку
            raise ValueError("В сообщении отсутствует поле message_type (тип сообщения)")
        message_type = MessageType(str(raw_type)) # Тип сообщения

        payload = data.get("payload") # Содержимое сообщения в зависимости от типа сообщения
        if payload is not None and not isinstance(payload, dict): # Если содержимое сообщения не является словарем, то выбрасываем ошибку
            raise ValueError("Поле payload должно быть объектом (словарь)")

        status_raw = data.get("status") # Статус сообщения
        status = Status(str(status_raw)) if status_raw is not None else None # Статус сообщения

        return cls( # Создание объекта из словаря
            message_type=message_type,
            message_id=_optional_id(data.get("message_id"), field="message_id"), # Идентификатор сообщения
            timestamp=_optional_str(data.get("timestamp")), # Время сообщения
            actuator_id=_optional_id(data.get("actuator_id"), field="actuator_id"), # Идентификатор исполнительного механизма
            command_id=_optional_id(data.get("command_id"), field="command_id"), # Идентификатор команды
            payload=payload, # Содержимое сообщения в зависимости от типа сообщения
            status=status, # Статус сообщения
            error_code=_optional_str(data.get("error_code")), # Код ошибки
            description=_optional_str(data.get("description")), # Описание сообщения
        )

_id_counter = 0 # Счётчик идентификаторов сообщений (0, 1, 2, …)

"""Выделение нового идентификатора сообщения"""
def alloc_id() -> int:
    global _id_counter
    value = _id_counter # Выделение нового идентификатора сообщения
    _id_counter += 1
    return value # Возвращение нового идентификатора сообщения

"""Сброс счётчика идентификаторов сообщений"""
def reset_ids() -> None:
    global _id_counter
    _id_counter = 0 # Сброс счётчика идентификаторов сообщений

"""Генерация временной метки в формате UTC"""
def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat() # Генерация временной метки в формате UTC

"""Генерация сообщения PING"""
def make_ping(*, message_id: int | None = None, command_id: int | None = None) -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(),
        timestamp=utc_timestamp(), # Время сообщения
        command_id=command_id, # Идентификатор команды
        payload={"service_type": ServiceType.PING.value}, # Содержимое сообщения в зависимости от типа сообщения
    )

"""Генерация сообщения PONG"""
def make_pong(*, message_id: int | None = None, command_id: int | None = None, reply_to: int | None = None) -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(), # Идентификатор сообщения
        timestamp=utc_timestamp(), # Время сообщения
        command_id=command_id if command_id is not None else reply_to,
        payload={"service_type": ServiceType.PONG.value}, # Содержимое сообщения в зависимости от типа сообщения
    )

"""Генерация сообщения GET_ACTUATORS"""
def make_get_actuators(*, message_id: int | None = None, command_id: int | None = None) -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(), # Идентификатор сообщения
        timestamp=utc_timestamp(), # Время сообщения
        command_id=command_id if command_id is not None else alloc_id(),
        payload={"service_type": ServiceType.GET_ACTUATORS.value}, # Содержимое сообщения в зависимости от типа сообщения
    )

"""Генерация сообщения ACTUATORS_LIST"""
def make_actuators_list(actuators: list[Any], *, message_id: int | None = None, command_id: int | None = None) -> AppMessage:
    return AppMessage(
        message_type=MessageType.SERVICE, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(), # Идентификатор сообщения
        timestamp=utc_timestamp(), # Время сообщения
        command_id=command_id, # Идентификатор команды
        payload={"service_type": ServiceType.ACTUATORS_LIST.value, "actuators": actuators}, # Содержимое сообщения в зависимости от типа сообщения
    )

_MOTION_PARAM_KEYS = ("position", "speed", "direction") # Ключи параметров движения

"""Добавление параметров движения"""
def _apply_motion_params(body: dict[str, Any], *, position: int | float | None = None, speed: int | float | None = None, direction: Direction | None = None) -> None:
    if position is not None:
        body["position"] = position
    if speed is not None: # Если скорость не None, то добавляем в payload
        body["speed"] = speed
    if direction is not None: # Если направление не None, то добавляем в payload
        body["direction"] = direction.value

"""Копирование параметров движения"""
def motion_params_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in _MOTION_PARAM_KEYS if key in payload} # Возвращение параметров движения из payload

"""Генерация сообщения COMMAND"""
def make_command(action: Action, *, actuator_id: int | None = None, command_id: int | None = None, position: int | float | None = None, speed: int | float | None = None, direction: Direction | None = None, message_id: int | None = None) -> AppMessage:
    body: dict[str, Any] = {"action": action.value} # Содержимое сообщения в зависимости от типа сообщения
    _apply_motion_params(body, position=position, speed=speed, direction=direction) # Добавление параметров движения в payload
    return AppMessage(
        message_type=MessageType.COMMAND, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(), # Идентификатор сообщения
        timestamp=utc_timestamp(), # Время сообщения
        actuator_id=actuator_id, # Идентификатор исполнительного механизма
        command_id=command_id if command_id is not None else alloc_id(),
        payload=body, # Содержимое сообщения в зависимости от типа сообщения
    )

"""Генерация сообщения TELEMETRY"""
def make_telemetry(state: State, error_state: bool, *, actuator_id: int | None = None, position: int | float | None = None, speed: int | float | None = None, direction: Direction | None = None, message_id: int | None = None, command_id: int | None = None) -> AppMessage:
    body: dict[str, Any] = {"state": state.value, "error_state": error_state} # Содержимое сообщения в зависимости от типа сообщения
    _apply_motion_params(body, position=position, speed=speed, direction=direction) # Добавление параметров движения в payload
    return AppMessage(
        message_type=MessageType.TELEMETRY, # Тип сообщения
        message_id=message_id if message_id is not None else alloc_id(), # Идентификатор сообщения
        timestamp=utc_timestamp(), # Время сообщения
        actuator_id=actuator_id, # Идентификатор исполнительного механизма
        command_id=command_id, # Идентификатор команды
        payload=body, # Содержимое сообщения в зависимости от типа сообщения
    )

"""Проверка сообщения"""
def validate_message(message: AppMessage) -> None:
    payload = message.payload or {} # Содержимое сообщения в зависимости от типа сообщения
    if message.message_type == MessageType.COMMAND: # Если тип сообщения COMMAND
        action_raw = payload.get("action") # Действие
        if action_raw is None: # Если действие отсутствует, то выбрасываем ошибку
            raise ValueError("Для command обязательно поле action")
        try:
            Action(str(action_raw)) # Действие
        except ValueError as exc: # Если действие не является допустимым, то выбрасываем ошибку
            raise ValueError(f"Недопустимое значение action: {action_raw!r}") from exc
        _validate_id(message.actuator_id, "actuator_id", required=False)
        _validate_motion_params_optional(payload)
        return

    if message.message_type == MessageType.RESPONSE: # Если тип сообщения RESPONSE
        if message.status is None: # Если статус отсутствует, то выбрасываем ошибку
            raise ValueError("Для response обязательно поле status")
        _validate_id(message.command_id, "command_id", required=False) # Проверка идентификатора команды
        _validate_id(message.actuator_id, "actuator_id", required=False) # Проверка идентификатора исполнительного механизма
        return

    if message.message_type == MessageType.TELEMETRY: # Если тип сообщения TELEMETRY
        if payload.get("state") is None: # Если состояние отсутствует, то выбрасываем ошибку
            raise ValueError("Для telemetry обязательно поле state")
        try:
            State(str(payload["state"])) # Состояние
        except ValueError as exc: # Если состояние не является допустимым, то выбрасываем ошибку
            raise ValueError(f"Недопустимое значение state: {payload['state']!r}") from exc
        if "error_state" not in payload: # Если поле error_state отсутствует, то выбрасываем ошибку
            raise ValueError("Для telemetry обязательно поле error_state")
        if not isinstance(payload["error_state"], bool): # Если поле error_state не является логическим значением, то выбрасываем ошибку
            raise ValueError("Поле error_state должно быть логическим значением")
        _validate_id(message.actuator_id, "actuator_id", required=False)
        _validate_motion_params_optional(payload)
        return

    if message.message_type == MessageType.DIAGNOSTIC: # Если тип сообщения DIAGNOSTIC
        level_raw = payload.get("level") # Уровень диагностики
        if level_raw is None: # Если уровень диагностики отсутствует, то выбрасываем ошибку
            raise ValueError("Для diagnostic обязательно поле level")
        try:
            Level(str(level_raw)) # Уровень диагностики
        except ValueError as exc: # Если уровень диагностики не является допустимым, то выбрасываем ошибку
            raise ValueError(f"Недопустимое значение level: {level_raw!r}") from exc
        return

    if message.message_type == MessageType.SERVICE: # Если тип сообщения SERVICE
        service_raw = payload.get("service_type") # Тип сервиса
        if service_raw is None: # Если тип сервиса отсутствует, то выбрасываем ошибку
            raise ValueError("Для service обязательно поле service_type")
        try:
            service_type = ServiceType(str(service_raw)) # Тип сервиса
        except ValueError as exc: # Если тип сервиса не является допустимым, то выбрасываем ошибку
            raise ValueError(f"Недопустимое значение service_type: {service_raw!r}") from exc
        if service_type == ServiceType.GET_ACTUATORS: # Если тип сервиса GET_ACTUATORS
            if message.actuator_id is not None: # Если идентификатор исполнительного механизма не None, то выбрасываем ошибку
                raise ValueError("Для get_actuators поле actuator_id не задаётся")
        elif service_type == ServiceType.ACTUATORS_LIST: # Если тип сервиса ACTUATORS_LIST
            if message.actuator_id is not None: # Если идентификатор исполнительного механизма не None, то выбрасываем ошибку
                raise ValueError("Для actuators_list поле actuator_id не задаётся")
            _validate_actuators_array(payload.get("actuators")) # Проверка массива исполнительных механизмов
        return

    raise ValueError(f"Неизвестный message_type: {message.message_type!r}") # Неизвестный тип сообщения

"""Проверка параметров движения"""
def _validate_motion_params_optional(payload: dict[str, Any]) -> None:
    if "position" in payload: # Если поле position в payload, то проверяем на число
        _validate_motion_number(payload["position"], "position")
    if "speed" in payload: # Если поле speed в payload, то проверяем на число
        _validate_motion_number(payload["speed"], "speed")
    if "direction" in payload: # Если поле direction в payload, то проверяем на направление
        raw = payload["direction"]
        if raw is None: # Если поле direction None, то выбрасываем ошибку
            raise ValueError("Поле direction не может быть null")
        try:
            Direction(str(raw)) # Направление
        except ValueError as exc: # Если направление не является допустимым, то выбрасываем ошибку
            raise ValueError(
                "direction должен быть forward (вперёд) или backward (назад)"
            ) from exc

"""Проверка числа"""
def _validate_motion_number(value: Any, field: str) -> None:
    if value is None: # Если значение None, то выбрасываем ошибку
        raise ValueError(f"Поле {field} не может быть null")
    if isinstance(value, bool): # Если значение является логическим значением, то выбрасываем ошибку
        raise ValueError(f"{field} должно быть числом")
    if isinstance(value, (int, float)): # Если значение является целым или вещественным числом, то пропускаем
        return
    if isinstance(value, str): # Если значение является строкой, то проверяем на число
        try:
            float(value) # Преобразование значения в число
        except ValueError as exc: # Если значение не является числом, то выбрасываем ошибку
            raise ValueError(f"{field} должно быть числом: {value!r}") from exc
        return
    raise ValueError(f"{field} должно быть числом: {value!r}") # Неизвестное значение

"""Проверка строкового значения"""
def _optional_str(value: Any) -> str | None:
    if value is None: # Если значение None, то возвращаем None
        return None
    return str(value) # Преобразование значения в строку

"""Разбор id из JSON поле может отсутствовать или быть строкой"""
def _optional_id(value: Any, *, field: str) -> int | None:
    if value is None: # Если значение None, то возвращаем None
        return None
    if isinstance(value, bool): # Если значение является логическим значением, то выбрасываем ошибку
        raise ValueError(f"{field} не может быть логическим значением")
    if isinstance(value, int): # Если значение является целым числом, то проверяем на отрицательность
        if value < 0:
            raise ValueError(f"{field} не может быть отрицательным")
        return value
    if isinstance(value, str) and value.isdigit(): # Если значение является строкой и содержит только цифры, то преобразуем в целое число
        return int(value) # Преобразование значения в целое число
    raise ValueError(f"{field} должен быть целым числом >= 0: {value!r}")

"""Проверка id в уже собранном сообщении обязательность и >= 0"""
def _validate_id(value: int | None, field: str, *, required: bool) -> None:
    if value is None: # Если значение None, то проверяем на обязательность
        if required: # Если значение обязательно, то выбрасываем ошибку
            raise ValueError(f"Обязательно поле {field}")
        return
    if value < 0: # Если значение отрицательное, то выбрасываем ошибку
        raise ValueError(f"{field} не может быть отрицательным")

"""Проверка массива исполнительных механизмов"""
def _validate_actuators_array(actuators: Any) -> None:
    if not isinstance(actuators, list): # Если массив исполнительных механизмов не является списком, то выбрасываем ошибку
        raise ValueError("Для actuators_list обязателен массив actuators")
    for index, item in enumerate(actuators): # Проверяем каждый элемент массива исполнительных механизмов
        if isinstance(item, str): # Если элемент массива исполнительных механизмов является строкой, то проверяем на пустоту
            if not item.strip(): # Если строка пустая, то выбрасываем ошибку
                raise ValueError(f"actuators[{index}]: имя не может быть пустым")
            continue
        if isinstance(item, dict): # Если элемент массива исполнительных механизмов является словарём, то проверяем на пустоту
            raw_name = item.get("name") # Имя исполнительного механизма
            if raw_name is None or not str(raw_name).strip(): # Если имя исполнительного механизма пустое, то выбрасываем ошибку
                raise ValueError(f"actuators[{index}]: обязательно непустое поле name")
            if "id" in item: # Если поле id в словаре, то проверяем на целочисленность
                _optional_id(item["id"], field=f"actuators[{index}].id")
            continue
        raise ValueError(f"actuators[{index}] должен быть строкой (имя) или объектом с полем name")
