"""Проверки готовности операций и пояснения для оператора"""

from __future__ import annotations

from typing import Any

from config.config_validator import validate_config
from protocol.message import AppMessage
from core.telemetry_display import validate_telemetry_message


def check_config_for_connect(config: dict[str, Any]) -> tuple[bool, str]:
    """Проверка конфигурации перед подключением"""
    try:
        validate_config(config)
    except ValueError as exc:
        return False, f"Конфигурация: {exc}"
    transport = str(config.get("active_transport", "usb"))
    if transport == "usb" and not str(config.get("usb", {}).get("port", "")).strip():
        return False, "Укажите COM-порт для USB"
    if transport == "usb":
        return True, f"Будет открыт порт {config['usb']['port']} ({config['usb']['baudrate']} бод)"
    if transport == "wifi":
        wifi = config["wifi"]
        return True, f"Будет TCP {wifi['host']}:{wifi['port']}"
    gsm = config.get("gsm", {})
    if str(gsm.get("mode", "mqtt")) == "tcp":
        return True, f"Будет GSM TCP {gsm.get('host')}:{gsm.get('port')}"
    return True, f"Будет GSM MQTT {gsm.get('broker_host')}:{gsm.get('broker_port')}"


def explain_send_blocked(
    *,
    link_connected: bool,
    actuator_count: int,
    has_actuator: bool,
    has_action: bool,
    action_is_move: bool,
    position_ok: bool,
    speed_ok: bool,
) -> str:
    if not link_connected:
        return "Команда недоступна: нет связи с контроллером"
    if actuator_count == 0:
        return "Команда недоступна: контроллер не вернул механизмы"
    if not has_actuator:
        return "Команда недоступна: выберите механизм"
    if not has_action:
        return "Команда недоступна: выберите действие"
    if action_is_move and not position_ok:
        return "Исправьте положение: целое положительное число или оставьте пустым"
    if action_is_move and not speed_ok:
        return "Исправьте скорость: целое положительное число или оставьте пустым (по умолчанию)"
    return "Можно отправить команду"


def explain_stop_blocked(*, link_connected: bool, actuator_count: int, has_actuator: bool) -> str:
    if not link_connected:
        return "Остановка недоступна: нет связи с контроллером"
    if actuator_count == 0:
        return "Остановка недоступна: нет механизмов"
    if not has_actuator:
        return "Остановка недоступна: выберите механизм"
    return "Можно отправить остановку"


def check_telemetry_issues(message: AppMessage) -> list[str]:
    return validate_telemetry_message(message)
