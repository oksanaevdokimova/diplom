"""Проверка назначения id механизмам и реестра."""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import unittest # Модуль для работы с тестами
from protocol.actuators import ActuatorRegistry, entries_to_actuators_payload # Модуль для работы с механизмами
from protocol.framing import parse_line, serialize_line # Модуль для работы с фреймированием
from protocol.message import make_actuators_list, make_get_actuators, reset_ids, validate_message # Модуль для работы с сообщениями

"""Проверка назначения id механизмам и реестра"""
class ActuatorRegistryTests(unittest.TestCase):
    """Инициализация теста"""
    def setUp(self) -> None:
        reset_ids() # Сбрасываем id механизмов

    """Проверка назначения id механизмам по порядку из строк"""
    def test_assign_ids_by_order_from_strings(self) -> None:
        registry = ActuatorRegistry() # Создаём реестр механизмов
        entries = registry.load_raw_actuators(["Поворот", "Подъём"]) # Загружаем механизмы из строк
        self.assertEqual([e.id for e in entries], [0, 1]) # Проверяем, что id механизмов равны [0, 1]
        self.assertEqual(entries[0].name, "Поворот") # Проверяем, что name механизма равен "Поворот"
        self.assertEqual(entries[1].name, "Подъём") # Проверяем, что name механизма равен "Подъём"
        self.assertIs(registry.get(0), entries[0]) # Проверяем, что механизм с id 0 равен entries[0]
        self.assertIsNone(registry.get(99)) # Проверяем, что механизм с id 99 равен None

    """Проверка назначения id механизмам по порядку из объектов с name"""
    def test_assign_ids_from_objects_with_name(self) -> None:
        registry = ActuatorRegistry() # Создаём реестр механизмов
        entries = registry.load_raw_actuators([{"name": "Grip"}]) # Загружаем механизмы из объектов с name
        self.assertEqual(entries[0].id, 0) # Проверяем, что id механизма равен 0
        self.assertEqual(entries[0].name, "Grip") # Проверяем, что name механизма равен "Grip"

    """Проверка загрузки механизмов из сообщения контроллера"""
    def test_load_from_controller_message(self) -> None:
        request = make_get_actuators() # Создаём сообщение запроса механизмов
        response = make_actuators_list(["Grip", "Rotate"], command_id=request.command_id) # Создаём сообщение ответа с механизмами
        validate_message(response)
        registry = ActuatorRegistry() # Создаём реестр механизмов
        entries = registry.load_from_controller_message(response) # Загружаем механизмы из сообщения контроллера
        self.assertEqual(len(entries), 2) # Проверяем, что количество механизмов равно 2
        self.assertEqual(entries[0].name, "Grip") # Проверяем, что name механизма равен "Grip"
        self.assertEqual(entries[1].id, 1) # Проверяем, что id механизма равен 1

    """Проверка создания сообщения с механизмами с id"""
    def test_app_actuators_list_with_ids(self) -> None:
        registry = ActuatorRegistry() # Создаём реестр механизмов
        registry.load_raw_actuators(["A", "B"]) # Загружаем механизмы из строк
        catalog = make_actuators_list(entries_to_actuators_payload(list(registry.entries))) # Создаём сообщение с механизмами с id
        validate_message(catalog) # Проверяем сообщение
        parsed = parse_line(serialize_line(catalog).decode("utf-8").strip()) # Разбираем сообщение
        items = parsed.payload["actuators"] # Получаем список механизмов из payload
        self.assertEqual(items[0], {"id": 0, "name": "A"}) # Проверяем, что первый механизм равен {"id": 0, "name": "A"}
        self.assertEqual(items[1]["name"], "B") # Проверяем, что второй механизм равен {"name": "B"}

    """Проверка отклонения сообщения с механизмами с id"""
    def test_get_actuators_rejects_actuator_id(self) -> None:
        bad = make_get_actuators() # Создаём сообщение запроса механизмов
        bad.actuator_id = 0 # Устанавливаем id механизма в 0
        with self.assertRaises(ValueError): # Проверяем, что ValueError выбрасывается
            validate_message(bad)

    """Проверка отклонения сообщения с механизмами с пустым name"""
    def test_empty_name_rejected(self) -> None:
        with self.assertRaises(ValueError): # Проверяем, что ValueError выбрасывается
            validate_message(make_actuators_list(["  "])) # Проверяем сообщение

"""Запуск тестов"""
if __name__ == "__main__":
    unittest.main()
