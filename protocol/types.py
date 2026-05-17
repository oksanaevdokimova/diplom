"""Перечисления прикладного протокола"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from enum import Enum # Перечисления

"""Типы сообщений"""
class MessageType(str, Enum):
    COMMAND = "command"
    RESPONSE = "response"
    TELEMETRY = "telemetry"
    DIAGNOSTIC = "diagnostic"
    SERVICE = "service"

"""Действия"""
class Action(str, Enum):
    MOVE = "move" 
    STOP = "stop"

"""Направление движения"""
class Direction(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"

"""Статусы"""
class Status(str, Enum):
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"

"""Состояния"""
class State(str, Enum):
    READY = "ready"
    MOVING = "moving"
    STOPPED = "stopped"

"""Уровни диагностики"""
class Level(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

"""Типы сервисов"""
class ServiceType(str, Enum):
    PING = "ping"
    PONG = "pong"
    GET_ACTUATORS = "get_actuators"
    ACTUATORS_LIST = "actuators_list"
