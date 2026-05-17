"""Проверка protocol: сериализация, разбор по частям, ping/pong"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import unittest # Модуль для работы с тестами
from protocol.framing import LineFramer, parse_line, serialize_line # Модуль для работы с фреймированием
from protocol.message import ( # Модуль для работы с сообщениями
    AppMessage,
    make_command,
    make_ping,
    make_pong,
    make_telemetry,
    motion_params_from_payload,
    reset_ids,
    validate_message,
)
from protocol.types import Action, Direction, MessageType, ServiceType, State, Status # Модуль для работы с типами

"""Проверка protocol"""
class ProtocolTests(unittest.TestCase):
    """Инициализация теста"""
    def setUp(self) -> None:
        reset_ids()

    """Проверка ping/pong"""
    def test_ping_round_trip(self) -> None:
        original = make_ping() # Создаём сообщение ping
        self.assertEqual(original.message_id, 0) # Проверяем, что message_id равен 0
        restored = parse_line(serialize_line(original).decode("utf-8").rstrip("\n")) # Разбираем сообщение ping
        self.assertEqual(restored.message_type, MessageType.SERVICE) # Проверяем, что message_type равен MessageType.SERVICE
        self.assertEqual(restored.payload["service_type"], ServiceType.PING.value) # Проверяем, что payload["service_type"] равен ServiceType.PING.value

    """Проверка command move с необязательными полями"""
    def test_command_move_optional_fields(self) -> None:
        cmd = make_command(Action.MOVE, actuator_id=0, position=100, speed=50) # Создаём сообщение command move
        validate_message(cmd) # Проверяем сообщение
        line = serialize_line(cmd).decode("utf-8") # Сериализуем сообщение
        parsed = parse_line(line.strip()) # Разбираем сообщение
        self.assertEqual(parsed.payload["action"], Action.MOVE.value) # Проверяем, что payload["action"] равен Action.MOVE.value
        self.assertEqual(parsed.payload["position"], 100) # Проверяем, что payload["position"] равен 100
        self.assertEqual(parsed.actuator_id, 0) # Проверяем, что actuator_id равен 0

    """Проверка response с обязательным полем status"""
    def test_response_requires_status(self) -> None:
        bad = AppMessage(message_type=MessageType.RESPONSE, command_id=0) # Создаём сообщение response
        with self.assertRaises(ValueError): # Проверяем, что ValueError выбрасывается
            validate_message(bad) # Проверяем сообщение

    """Проверка telemetry с обязательными полями state и error_state"""
    def test_telemetry_requires_state_and_error_state(self) -> None:
        ok = AppMessage(message_type=MessageType.TELEMETRY, payload={"state": "ready", "error_state": False}) # Создаём сообщение telemetry
        validate_message(ok) # Проверяем сообщение

    """Проверка command stop без motion_params"""
    def test_command_stop_without_motion_params(self) -> None:
        cmd = make_command(Action.STOP, actuator_id=0) # Создаём сообщение command stop
        validate_message(cmd)
        self.assertNotIn("position", cmd.payload) # Проверяем, что position не в payload

    """Проверка telemetry с эхом motion_params"""
    def test_telemetry_echoes_motion_params(self) -> None:
        cmd = make_command(Action.MOVE, actuator_id=0, position=100, speed=50, direction=Direction.FORWARD) # Создаём сообщение command move
        motion = motion_params_from_payload(cmd.payload) # Получаем motion_params из payload
        tel = make_telemetry(State.MOVING, False, actuator_id=0, position=motion.get("position"), speed=motion.get("speed"), direction=Direction(str(motion["direction"]))) # Создаём сообщение telemetry
        validate_message(tel) # Проверяем сообщение
        parsed = parse_line(serialize_line(tel).decode("utf-8").strip()) # Разбираем сообщение
        self.assertEqual(parsed.payload["position"], 100) # Проверяем, что position равен 100
        self.assertEqual(parsed.payload["speed"], 50) # Проверяем, что speed равен 50
        self.assertEqual(parsed.payload["direction"], "forward") # Проверяем, что direction равен "forward"
        self.assertNotIn("action", parsed.payload) # Проверяем, что action не в payload

    """Проверка invalid direction rejected"""
    def test_invalid_direction_rejected(self) -> None:
        bad = AppMessage(message_type=MessageType.COMMAND, payload={"action": "move", "direction": "left"}) # Создаём сообщение command
        with self.assertRaises(ValueError): # Проверяем, что ValueError выбрасывается
            validate_message(bad)

    """Проверка feed_bytes с разделением на части"""
    def test_feed_bytes_split_chunks(self) -> None:
        ping = make_ping() # Создаём сообщение ping
        raw = serialize_line(ping) # Сериализуем сообщение
        framer = LineFramer() # Создаём фреймер
        first = framer.feed_bytes(raw[:10]) # Разбиваем сообщение на части
        second = framer.feed_bytes(raw[10:]) # Разбиваем сообщение на части
        self.assertEqual(first, []) # Проверяем, что first равен []
        self.assertEqual(len(second), 1) # Проверяем, что len(second) равен 1
        msg = parse_line(second[0]) # Разбираем сообщение
        self.assertEqual(msg.payload["service_type"], ServiceType.PING.value) # Проверяем, что payload["service_type"] равен ServiceType.PING.value

    """Проверка pong reply"""
    def test_pong_reply(self) -> None:
        ping = make_ping(command_id=5) # Создаём сообщение ping
        pong = make_pong(reply_to=ping.message_id) # Создаём сообщение pong
        self.assertEqual(pong.command_id, ping.message_id) # Проверяем, что command_id равен message_id
        self.assertEqual(pong.payload["service_type"], ServiceType.PONG.value) # Проверяем, что payload["service_type"] равен ServiceType.PONG.value
        roundtrip = parse_line(serialize_line(pong).decode("utf-8").strip()) # Разбираем сообщение
        self.assertEqual(roundtrip.payload["service_type"], ServiceType.PONG.value) # Проверяем, что payload["service_type"] равен ServiceType.PONG.value

    """Проверка response status values"""
    def test_response_status_values(self) -> None:
        resp = AppMessage(message_type=MessageType.RESPONSE, command_id=1, status=Status.ACCEPTED) # Создаём сообщение response
        validate_message(resp) # Проверяем сообщение
        parsed = parse_line(serialize_line(resp).decode("utf-8").strip()) # Разбираем сообщение
        self.assertEqual(parsed.status, Status.ACCEPTED) # Проверяем, что status равен Status.ACCEPTED

"""Запуск тестов"""
if __name__ == "__main__":
    unittest.main()
