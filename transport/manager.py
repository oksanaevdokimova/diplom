"""Фабрика транспорта по активному каналу из конфигурации"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from typing import Any # Универсальный тип для значений в словаре конфигурации
from transport.base import BaseTransport # Базовый класс транспорта
from transport.mqtt_transport import MqttTransport # Транспорт MQTT
from transport.serial_transport import SerialTransport # Транспорт Serial
from transport.tcp_transport import TcpTransport # Транспорт TCP

"""Создать экземпляр SerialTransport, TcpTransport или MqttTransport"""
def create_transport(config: dict[str, Any], parent: Any = None) -> BaseTransport:
    connect_timeout = float(config.get("timeout_seconds", 60))
    active = config.get("active_transport") # Получение активного транспорта из конфигурации
    if active == "usb": # Если активный транспорт USB
        usb = config["usb"] # Получение настроек USB из конфигурации
        return SerialTransport(port=str(usb["port"]), baudrate=int(usb["baudrate"]), parent=parent) # Создание транспорта Serial
    if active == "wifi": # Если активный транспорт WiFi
        wifi = config["wifi"] # Получение настроек WiFi из конфигурации
        return TcpTransport(
            host=str(wifi["host"]),
            port=int(wifi["port"]),
            connect_timeout=connect_timeout,
            channel_label="Wi-Fi TCP",
            parent=parent,
        )
    if active == "gsm": # Если активный транспорт GSM
        gsm = config["gsm"] # Получение настроек GSM из конфигурации
        mode = gsm.get("mode") # Получение режима GSM из конфигурации
        if mode == "tcp": # Если режим TCP
            return TcpTransport(
                host=str(gsm["host"]),
                port=int(gsm["port"]),
                connect_timeout=connect_timeout,
                channel_label="GSM TCP",
                parent=parent,
            )
        if mode == "mqtt":
            return MqttTransport(
                broker_host=str(gsm["broker_host"]),
                broker_port=int(gsm["broker_port"]),
                topic_command=str(gsm["topic_command"]),
                topic_messages=str(gsm["topic_messages"]),
                connect_timeout=connect_timeout,
                parent=parent,
            )
        raise ValueError(f"Неизвестный режим GSM: {mode!r}") # Выбрасываем ошибку, если режим GSM не известен
    raise ValueError(f"Неизвестный active_transport: {active!r}") # Выбрасываем ошибку, если активный транспорт не известен
