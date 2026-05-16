"""ГЛАВНОЕ ОКНО"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
from copy import deepcopy # Функция для копирования вложенных структур при слиянии конфигов
from typing import Any # Универсальный тип для значений в словаре конфигурации
from PySide6.QtCore import QEvent, Qt # Базовый класс событий Qt (например закрытие окна в closeEvent)
from PySide6.QtGui import QGuiApplication, QKeyEvent # Сведения о дисплее, события клавиатуры
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout # Главное окно, центральный виджет, вертикальный layout
from ui.panels.connection_panel import ConnectionPanel # Панель подключения

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
        layout.setSpacing(15) # Установка отступа между панелями
        self.connection_panel = ConnectionPanel(self._config, self) # Создание панели подключения
        self.connection_panel.config_saved.connect(self._on_config_saved) # Соединение сигнала config_saved с методом _on_config_saved
        layout.addWidget(self.connection_panel)
        layout.addStretch() # Добавление пустого пространства для растяжения (ВРЕМЕННО)
        self.setCentralWidget(central_widget) # Установка центрального виджета в окно

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