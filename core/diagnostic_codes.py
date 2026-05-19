"""Реестр кодов диагностики приложения (формат PREFIX-NNN)."""

from __future__ import annotations

from protocol import error_codes as wire
from protocol.types import Level

APP_001 = "APP-001"
APP_002 = "APP-002"
APP_003 = "APP-003"
APP_004 = "APP-004"
APP_005 = "APP-005"

LINK_001 = "LINK-001"
LINK_002 = "LINK-002"
LINK_003 = "LINK-003"
LINK_004 = "LINK-004"
LINK_005 = "LINK-005"
LINK_006 = "LINK-006"

PROTO_001 = "PROTO-001"
PROTO_002 = "PROTO-002"
PROTO_003 = "PROTO-003"
PROTO_004 = "PROTO-004"
PROTO_005 = "PROTO-005"
PROTO_006 = "PROTO-006"

CMD_001 = "CMD-001"
CMD_002 = "CMD-002"
CMD_003 = "CMD-003"
CMD_004 = "CMD-004"
CMD_005 = "CMD-005"

ACT_001 = "ACT-001"
ACT_002 = "ACT-002"
ACT_003 = "ACT-003"
ACT_004 = "ACT-004"
ACT_005 = "ACT-005"
ACT_006 = "ACT-006"

TEL_001 = "TEL-001"

TRN_001 = "TRN-001"
TRN_002 = "TRN-002"
TRN_003 = "TRN-003"
TRN_004 = "TRN-004"
TRN_005 = "TRN-005"

CTRL_001 = "CTRL-001"
CTRL_002 = "CTRL-002"
CTRL_003 = "CTRL-003"

_WIRE_TO_DISPLAY: dict[int, str] = {
    wire.WIRE_APP_CONFIG: APP_001,
    wire.WIRE_APP_CMD_BLOCKED: APP_002,
    wire.WIRE_APP_CMD_BUILD: APP_003,
    wire.WIRE_APP_CONNECT_FIELDS: APP_004,
    wire.WIRE_APP_INPUT_FIELD: APP_005,
    wire.WIRE_LINK_CONNECTING: LINK_001,
    wire.WIRE_LINK_READY: LINK_002,
    wire.WIRE_LINK_LOST: LINK_003,
    wire.WIRE_LINK_CMD_NO_CONN: LINK_004,
    wire.WIRE_LINK_CMD_PONG: LINK_005,
    wire.WIRE_LINK_DISCONNECTED: LINK_006,
    wire.WIRE_PROTO_JSON: PROTO_001,
    wire.WIRE_PROTO_EMPTY: PROTO_002,
    wire.WIRE_PROTO_NOT_OBJECT: PROTO_003,
    wire.WIRE_PROTO_VALIDATION: PROTO_004,
    wire.WIRE_PROTO_UNEXPECTED_CMD: PROTO_005,
    wire.WIRE_PROTO_UNKNOWN_TYPE: PROTO_006,
    wire.WIRE_CMD_TIMEOUT: CMD_001,
    wire.WIRE_CMD_ORPHAN: CMD_002,
    wire.WIRE_CMD_ACCEPTED: CMD_003,
    wire.WIRE_CMD_REJECTED: CMD_004,
    wire.WIRE_CMD_ERROR: CMD_005,
    wire.WIRE_ACT_LOADED: ACT_001,
    wire.WIRE_ACT_FAILED: ACT_002,
    wire.WIRE_ACT_EMPTY: ACT_003,
    wire.WIRE_ACT_TIMEOUT: ACT_004,
    wire.WIRE_ACT_INVALID: ACT_005,
    wire.WIRE_ACT_SEND_UNAVAILABLE: ACT_006,
    wire.WIRE_TEL_VALIDATION: TEL_001,
    wire.WIRE_TRN_NOT_CONNECTED: TRN_001,
    wire.WIRE_TRN_MODULE_MISSING: TRN_002,
    wire.WIRE_TRN_IO: TRN_003,
    wire.WIRE_TRN_INVALID_SOCKET: TRN_004,
    wire.WIRE_TRN_MQTT_PUBLISH: TRN_005,
    wire.WIRE_CTRL_INFO: CTRL_001,
    wire.WIRE_CTRL_WARN: CTRL_002,
    wire.WIRE_CTRL_ERROR: CTRL_003,
}

CODE_TITLES: dict[str, str] = {
    APP_001: "Конфигурация подключения отклонена",
    APP_002: "Команда заблокирована: нет связи",
    APP_003: "Ошибка сборки команды",
    APP_004: "Некорректные поля панели подключения",
    APP_005: "Некорректное значение в поле ввода",
    LINK_001: "Установка связи",
    LINK_002: "Связь установлена",
    LINK_003: "Связь потеряна",
    LINK_004: "Команда без соединения",
    LINK_005: "Нет pong после команды",
    LINK_006: "Отключение от контроллера",
    PROTO_001: "Ошибка JSON",
    PROTO_002: "Пустая строка протокола",
    PROTO_003: "Сообщение не объект JSON",
    PROTO_004: "Ошибка валидации протокола",
    PROTO_005: "Входящая command не ожидается",
    PROTO_006: "Неизвестный тип сообщения",
    CMD_001: "Таймаут ответа на команду",
    CMD_002: "Ответ без ожидающей команды",
    CMD_003: "Команда принята",
    CMD_004: "Команда отклонена",
    CMD_005: "Ошибка выполнения команды",
    ACT_001: "Список механизмов получен",
    ACT_002: "Ошибка списка механизмов",
    ACT_003: "Пустой список механизмов",
    ACT_004: "Таймаут actuators_list",
    ACT_005: "Некорректный actuators_list",
    ACT_006: "Запрос actuators_list не отправлен",
    TEL_001: "Ошибка валидации телеметрии",
    TRN_001: "Транспорт не подключён",
    TRN_002: "Нет модуля транспорта",
    TRN_003: "Ошибка ввода-вывода транспорта",
    TRN_004: "Некорректный сокет",
    TRN_005: "Ошибка публикации MQTT",
    CTRL_001: "Сообщение контроллера (info)",
    CTRL_002: "Предупреждение контроллера",
    CTRL_003: "Ошибка контроллера",
}


def display_code_from_wire(value: int | None, *, default: str) -> str:
    if value is None:
        return default
    return _WIRE_TO_DISPLAY.get(int(value), default)


def default_display_code_for_level(level: str) -> str:
    if level == "ERR":
        return CTRL_003
    if level == "WARN":
        return CTRL_002
    return CTRL_001


def default_display_code_for_diagnostic_level(level: Level) -> str:
    if level == Level.ERROR:
        return CTRL_003
    if level == Level.WARNING:
        return CTRL_002
    return CTRL_001
