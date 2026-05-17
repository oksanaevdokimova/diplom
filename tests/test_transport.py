"""Проверка TCP-транспорта и выбора транспорта"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import socket # Модуль для работы с сокетами
import threading # Модуль для работы с потоками
import unittest # Модуль для работы с тестами
from PySide6.QtCore import QCoreApplication # Мьютекс для синхронизации доступа к данным
from transport.manager import create_transport # Функция создания транспорта
from transport.mqtt_transport import MqttTransport # Транспорт MQTT
from transport.serial_transport import SerialTransport # Транспорт Serial
from transport.tcp_transport import TcpTransport # Транспорт TCP

"""Проверка наличия QCoreApplication"""
def _ensure_qapp() -> QCoreApplication:
    app = QCoreApplication.instance() # Получаем экземпляр QCoreApplication
    if app is None: # Если экземпляр не существует, то создаём новый
        app = QCoreApplication([]) # Создаём новый экземпляр QCoreApplication
    return app # Возвращаем экземпляр QCoreApplication

"""Эхо-сервер"""
class _EchoServer:
    """Инициализация эхо-сервера"""
    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создаём сокет
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Устанавливаем опцию SO_REUSEADDR
        self._sock.bind(("127.0.0.1", 0)) # Привязываем сокет к адресу
        self._sock.listen(1) # Начинаем слушать сокет
        self.host, self.port = self._sock.getsockname() # Получаем адрес и порт
        self._thread = threading.Thread(target=self._serve, daemon=True) # Создаём поток для обслуживания соединений
        self._thread.start() # Запускаем поток

    """Обслуживание соединений"""
    def _serve(self) -> None:
        conn, _ = self._sock.accept() # Принимаем соединение
        with conn: # Связываем соединение
            while True:
                data = conn.recv(4096) # Читаем данные из сокета
                if not data: # Если данные не получены, то выходим из цикла
                    break # Выходим из цикла
                conn.sendall(data) # Отправляем данные в сокет

    """Закрытие соединения"""
    def close(self) -> None:
        self._sock.close() # Закрываем сокет

"""Проверка создания транспорта"""
class TransportManagerTests(unittest.TestCase):
    """Проверка создания транспорта USB"""
    def test_create_usb(self) -> None:
        transport = create_transport(
            {
                "active_transport": "usb",
                "usb": {"port": "COM1", "baudrate": 115200},
            }
        )
        self.assertIsInstance(transport, SerialTransport)

    """Проверка создания транспорта WiFi"""
    def test_create_wifi(self) -> None:
        transport = create_transport(
            {
                "active_transport": "wifi",
                "wifi": {"host": "127.0.0.1", "port": 5000},
            }
        )
        self.assertIsInstance(transport, TcpTransport)

    """Проверка создания транспорта GSM MQTT"""
    def test_create_gsm_mqtt(self) -> None:
        transport = create_transport(
            {
                "active_transport": "gsm",
                "gsm": {
                    "mode": "mqtt",
                    "broker_host": "localhost",
                    "broker_port": 1883,
                    "topic_command": "cmd",
                    "topic_messages": "msg",
                },
            }
        )
        self.assertIsInstance(transport, MqttTransport)

    """Проверка создания транспорта GSM TCP"""
    def test_create_gsm_tcp(self) -> None:
        transport = create_transport(
            {
                "active_transport": "gsm",
                "gsm": {"mode": "tcp", "host": "127.0.0.1", "port": 5001},
            }
        )
        self.assertIsInstance(transport, TcpTransport)

"""Проверка TCP-транспорта"""
class TcpTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = _ensure_qapp() # Создаём экземпляр QCoreApplication

    """Проверка соединения, отправки и получения данных"""
    def test_connect_send_receive(self) -> None:
        server = _EchoServer() # Создаём экземпляр эхо-сервера
        received: list[bytes] = [] # Список для хранения полученных данных
        transport = TcpTransport(server.host, server.port) # Создаём экземпляр транспорта TCP
        try:
            transport.data_received.connect(received.append) # Подключаем сигнал приема данных к списку
            transport.connect() # Подключаемся к эхо-серверу
            deadline = 0.0 # Время начала ожидания
            import time # Модуль для работы с временем
            end = time.monotonic() + 3.0 # Время окончания ожидания
            while not transport.is_connected and time.monotonic() < end: # Пока не подключено и время не истекло
                self._app.processEvents() # Обрабатываем события Qt
                time.sleep(0.02) # Ждём 20 миллисекунд
            self.assertTrue(transport.is_connected, "TCP не подключился к эхо-серверу") # Проверяем, что соединение установлено
            payload = b"hello\n" # Создаём payload
            transport.send(payload) # Отправляем payload
            end = time.monotonic() + 3.0 # Время окончания ожидания
            while not received and time.monotonic() < end: # Пока не получены данные и время не истекло
                self._app.processEvents() # Обрабатываем события Qt
                time.sleep(0.02) # Ждём 20 миллисекунд
            self.assertEqual(received[0], payload) # Проверяем, что полученные данные совпадают с отправленными
        finally:
            transport.disconnect()
            server.close()

"""Запуск тестов"""
if __name__ == "__main__":
    unittest.main()
