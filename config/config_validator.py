"""ПРОВЕРКА СТРУКТУРЫ КОНФИГУРАЦИИ"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from typing import Any # Универсальный тип для значений в словаре конфигурации

"""Проверка: значение — положительное целое число"""
def _require_positive_int(name: str, value: Any) -> None: # name — имя поля в сообщении об ошибке
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0: # Если не целое число или не положительное
        raise ValueError(f"{name} должен быть положительным целым числом") # Ошибка: неверное значение

"""Проверка: значение — непустая строка"""
def _require_nonempty_str(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip(): # Если не строка или пустая строка
        raise ValueError(f"{name} должен быть непустой строкой") # Ошибка: неверное значение

"""Проверка: USB"""
def _validate_usb(usb: dict[str, Any]) -> None: # usb — словарь секции usb из конфигурации
    _require_nonempty_str("usb.port", usb.get("port")) # Проверяем, что port не пустая строка
    _require_positive_int("usb.baudrate", usb.get("baudrate")) # Проверяем, что baudrate положительное целое число

"""Проверка: WIFI"""
def _validate_wifi(wifi: dict[str, Any]) -> None: # wifi — словарь секции wifi из конфигурации
    _require_nonempty_str("wifi.host", wifi.get("host")) # Проверяем, что host не пустая строка
    _require_positive_int("wifi.port", wifi.get("port")) # Проверяем, что port положительное целое число

"""Проверка: GSM"""
def _validate_gsm(gsm: dict[str, Any]) -> None: # gsm — словарь секции gsm из конфигурации
    mode = gsm.get("mode") # Получаем значение mode из gsm
    if mode == "tcp": # Если tcp
        _require_nonempty_str("gsm.host (TCP)", gsm.get("host")) # Проверяем, что host не пустая строка
        _require_positive_int("gsm.port (TCP)", gsm.get("port")) # Проверяем, что port положительное целое число
        return
    elif mode == "mqtt": # Если mqtt
        _require_nonempty_str("gsm.broker_host", gsm.get("broker_host")) # Проверяем, что broker_host не пустая строка
        _require_positive_int("gsm.broker_port", gsm.get("broker_port")) # Проверяем, что broker_port положительное целое число
        _require_nonempty_str("gsm.topic_command", gsm.get("topic_command")) # Проверяем, что topic_command не пустая строка
        _require_nonempty_str("gsm.topic_messages", gsm.get("topic_messages")) # Проверяем, что topic_messages не пустая строка

"""Проверка: конфигурация"""
def validate_config(config: dict[str, Any]) -> None: # config — словарь конфигурации
    transport = config.get("active_transport") # В интерфейсе только выбор usb, wifi или gsm

    _require_positive_int("timeout_seconds", config.get("timeout_seconds")) # Проверяем, что timeout_seconds положительное целое число

    if transport == "usb": # Если usb
        usb = config.get("usb") # Получаем значение usb из конфигурации
        if not isinstance(usb, dict): # Если usb не словарь
            raise ValueError("Неверный раздел USB: в конфигурации должны быть настройки порта и скорости (поле usb).") # Ошибка: неверный тип
        _validate_usb(usb) # Проверяем, что usb корректный
    elif transport == "wifi": # Если wifi
        wifi = config.get("wifi") # Получаем значение wifi из конфигурации
        if not isinstance(wifi, dict): # Если wifi не словарь
            raise ValueError("Неверный раздел Wi‑Fi: в конфигурации должны быть адрес (хост) и порт (поле wifi).") # Ошибка: неверный тип
        _validate_wifi(wifi) # Проверяем, что wifi корректный
    elif transport == "gsm": # Если gsm
        gsm = config.get("gsm") # Получаем значение gsm из конфигурации
        if not isinstance(gsm, dict): # Если gsm не словарь
            raise ValueError("Неверный раздел GSM: в конфигурации должны быть настройки модуля — режим и параметры связи (поле gsm).") # Ошибка: неверный тип
        _validate_gsm(gsm) # Проверяем, что gsm корректный
