"""ГЛАВНОЕ ОКНО"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from copy import deepcopy # Функция для копирования вложенных структур при слиянии конфигов
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import QEvent, Qt # Базовый класс событий Qt (например закрытие окна в closeEvent)
from PySide6.QtGui import QGuiApplication, QKeyEvent # Сведения о дисплее, события клавиатуры
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout # Главное окно, центральный виджет, вертикальный layout
from ui.panels.connection_panel import ConnectionPanel # Панель подключения
from ui.panels.actuator_list_panel import ActuatorListPanel # Панель списка исполнительных механизмов
from ui.panels.connection_status_panel import ConnectionStatusPanel # Панель статуса подключения
from ui.panels.control_panel import ControlPanel # Панель управления
from ui.panels.diagnostic_panel import DiagnosticPanel # Панель диагностики
from ui.panels.log_panel import LogPanel # Панель лога
from ui.panels.telemetry_panel import TelemetryPanel # Панель телеметрии

"""Главное окно приложения"""
class MainWindow(QMainWindow):
    def __init__(self, config: dict[str, Any]) -> None: # Конструктор класса с конфигурацией
        super().__init__() # Вызов конструктора родительского класса (QMainWindow)
        self._config = deepcopy(config) # Создание копии конфигурации для дальнейшего использования (чтобы не менять переданную конфигурацию)
        self.setWindowTitle("Система управления исполнительными механизмами робота") # Установка заголовка окна
        screen = QGuiApplication.primaryScreen() # Получение основного экрана
        area = screen.availableGeometry() # Получение доступной области экрана
        self.setGeometry(area) # Установка геометрии окна
        self.setMinimumSize(area.width(), area.height()) # Установка минимального размера окна
        self._build_ui() # Построение интерфейса

    """Построение интерфейса"""
    def _build_ui(self) -> None:
        central_widget = QWidget() # Создание центрального виджета
        layout = QVBoxLayout(central_widget) # Создание вертикального расположения панелей
        layout.setContentsMargins(10, 10, 10, 10) # Установка отступов от главного окна до панелей
        layout.setSpacing(10) # Установка отступа между панелями по вертикали
        self.connection_panel = ConnectionPanel(self._config, self) # Создание панели подключения
        self.connection_panel.config_saved.connect(self._on_config_saved) # Соединение сигнала config_saved с методом _on_config_saved
        layout.addWidget(self.connection_panel)
        middle_row = QHBoxLayout() # Создание горизонтального расположения панелей
        middle_row.setSpacing(10) # Установка отступа между панелями по горизонтали
        self.actuator_list_panel = ActuatorListPanel(self) # Создание панели списка исполнительных механизмов
        middle_row.addWidget(self.actuator_list_panel, 2)  # ~25% ширины среднего ряда
        self.control_panel = ControlPanel(self) # Создание панели управления
        middle_row.addWidget(self.control_panel, 3)  # ~37% (было 50%)
        self.connection_panel.connection_changed.connect(self._on_connection_changed) # Соединение сигнала connection_changed с методом _on_connection_changed
        self.actuator_list_panel.actuators_changed.connect(self.control_panel.set_actuators) # Соединение сигнала actuators_changed с методом set_actuators
        right_column_widget = QWidget()
        right_column = QVBoxLayout(right_column_widget)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(10)
        right_column.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.telemetry_panel = TelemetryPanel(self)
        right_column.addWidget(self.telemetry_panel)
        self.connection_status_panel = ConnectionStatusPanel(self)
        right_column.addWidget(self.connection_status_panel)
        right_column.addStretch(1)
        middle_row.addWidget(right_column_widget, 3)
        layout.addLayout(middle_row, stretch=1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        self.diagnostic_panel = DiagnosticPanel(self)
        self.log_panel = LogPanel(self)
        bottom_row.addWidget(self.diagnostic_panel, 1)
        bottom_row.addWidget(self.log_panel, 1)
        layout.addLayout(bottom_row, stretch=1)
        self.setCentralWidget(central_widget) # Установка центрального виджета в окно

    """Обработка изменения состояния соединения"""
    def _on_connection_changed(self, connected: bool) -> None:
        self.actuator_list_panel.set_add_button_enabled(connected) # Установка доступности кнопки добавления механизмов
        if not connected:
            self.actuator_list_panel.clear_actuators() # Очистка списка механизмов

    """Обработка сохранения конфигурации"""
    def _on_config_saved(self, config: dict[str, Any]) -> None:
        self._config = deepcopy(config) # Обновление конфигурации

    """Получение конфигурации"""
    def config(self) -> dict[str, Any]:
        return self._config # Возвращение конфигурации

    """Обработка закрытия окна"""
    def closeEvent(self, event: QEvent) -> None:
        event.accept() # Принятие события

    """Обработка нажатия клавиши esc"""
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal() # Возвращение к обычному режиму
            return
        super().keyPressEvent(event) # Вызов родительского метода