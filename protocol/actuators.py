"""Отображение механизмов"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from dataclasses import dataclass # Класс для создания классов с автоматическим созданием методов
from typing import Any # Универсальный тип для значений в словаре конфигурации
from protocol.message import AppMessage # Импорт класса AppMessage
from protocol.types import ServiceType # Импорт типов сообщений

"""Механизм с id, назначенным приложением (0, 1, 2, …)"""
@dataclass(frozen=True)
class ActuatorEntry:
    id: int # Идентификатор механизма
    name: str # Имя механизма

    """Преобразование механизма в словарь"""
    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

"""Регистрация механизмов"""
class ActuatorRegistry:
    """Инициализация регистрации механизмов"""
    def __init__(self) -> None:
        self._entries: list[ActuatorEntry] = [] # Список механизмов

    """Очистка регистрации механизмов"""
    def clear(self) -> None:
        self._entries.clear() # Очистка списка механизмов

    """Получение списка механизмов"""
    @property
    def entries(self) -> tuple[ActuatorEntry, ...]:
        return tuple(self._entries) # Возвращение списка механизмов

    """Получение механизма по идентификатору"""
    def get(self, actuator_id: int) -> ActuatorEntry | None:
        for entry in self._entries:
            if entry.id == actuator_id:
                return entry
        return None

    """Загрузка механизмов из списка"""
    def load_raw_actuators(self, items: list[Any]) -> list[ActuatorEntry]:
        self._entries = [ActuatorEntry(id=index, name=_name_from_item(item, index)) for index, item in enumerate(items)]
        return list(self._entries) # Возвращение списка механизмов

    """Загрузка механизмов из сообщения"""
    def load_from_controller_message(self, message: AppMessage) -> list[ActuatorEntry]:
        raw = extract_controller_actuators(message)
        return self.load_raw_actuators(raw)

"""Список механизмов из actuators_list"""
def extract_controller_actuators(message: AppMessage) -> list[Any]:
    payload = message.payload or {}
    if payload.get("service_type") != ServiceType.ACTUATORS_LIST.value: # Если тип сообщения не равен ACTUATORS_LIST, то выбрасываем ошибку
        raise ValueError(f"Ожидался service_type actuators_list, получено: {payload.get('service_type')!r}")
    items = payload.get("actuators") # Получение списка механизмов из payload
    if not isinstance(items, list): # Если список механизмов не является списком, то выбрасываем ошибку
        raise ValueError("В actuators_list обязателен массив actuators")
    return items # Возвращение списка механизмов

"""Преобразование элемента списка механизмов в имя"""
def _name_from_item(item: Any, index: int) -> str:
    if isinstance(item, str): # Если элемент списка механизмов является строкой, то проверяем на пустоту
        name = item.strip()
        if not name: # Если имя пустое, то выбрасываем ошибку
            raise ValueError(f"actuators[{index}]: имя не может быть пустым")
        return name
    if isinstance(item, dict): # Если элемент списка механизмов является словарём, то проверяем на пустоту
        raw_name = item.get("name") # Получение имени из словаря
        if raw_name is None: # Если имя пустое, то выбрасываем ошибку
            raise ValueError(f"actuators[{index}]: обязательно поле name")
        name = str(raw_name).strip() # Преобразование имени в строку
        if not name: # Если имя пустое, то выбрасываем ошибку
            raise ValueError(f"actuators[{index}]: имя не может быть пустым")
        return name # Возвращение имени
    raise ValueError(f"actuators[{index}] должен быть строкой (имя) или объектом с полем name")
