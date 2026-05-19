"""Перечисления прикладного протокола"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from enum import Enum # Перечисления

class MessageType(str, Enum):
    """Тип сообщения в протоколе обмена"""
    COMMAND = "command"
    RESPONSE = "response"
    TELEMETRY = "telemetry"
    DIAGNOSTIC = "diagnostic"
    SERVICE = "service"

class Action(str, Enum):
    """Действие в команде управления"""
    MOVE = "move"
    STOP = "stop"

class Direction(str, Enum):
    """Направление движения механизма"""
    FORWARD = "forward"
    BACKWARD = "backward"

class Status(str, Enum):
    """Статус ответа контроллера на команду"""
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"

class State(str, Enum):
    """Состояние механизма в телеметрии"""
    READY = "ready"
    MOVING = "moving"
    STOPPED = "stopped"

class Level(str, Enum):
    """Уровень диагностического сообщения"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ServiceType(str, Enum):
    """Подтип служебного сообщения service"""
    PING = "ping"
    PONG = "pong"
    GET_ACTUATORS = "get_actuators"
    ACTUATORS_LIST = "actuators_list"
