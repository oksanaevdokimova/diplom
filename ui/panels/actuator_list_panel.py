"""Список исполнительных механизмов"""

from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

_PLUS_ICON = Path(__file__).resolve().parent.parent / "styles" / "icons" / "plus.svg"

"""Панель списка исполнительных механизмов"""
class ActuatorListPanel(QFrame):
    actuators_changed = Signal(list)

    """Конструктор панели списка исполнительных механизмов"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui() # Построение интерфейса

    """Структура панели списка исполнительных механизмов"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Разрешить растягивать панель по горизонтали и вертикали
        layout = QVBoxLayout(self) # Вертикальная раскладка для панели
        layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        layout.setSpacing(10) # Установка отступа между элементами по вертикали

        """Контейнер заголовка: слева название, справа кнопка"""
        header_container = QHBoxLayout()
        """Название панели"""
        self.title_label = QLabel("Исполнительные механизмы")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        header_container.addStretch(1) # Пустое место от названия панели до кнопки
        """Кнопка добавления механизмов"""
        self.add_button = QToolButton()
        self.add_button.setObjectName("iconButton")
        self.add_button.setIcon(QIcon(str(_PLUS_ICON))) # Иконка кнопки
        self.add_button.setIconSize(QSize(20, 20)) # Размер иконки
        self.add_button.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Не фокусироваться на кнопке
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor) # Курсор в виде руки
        self.add_button.setEnabled(False) # Доступна только после подключения к роботу
        header_container.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop) # Выравнивание по правому краю и по верху
        """Добавление контейнера заголовка в тело панели"""
        layout.addLayout(header_container)

        """Список исполнительных механизмов"""
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("actuatorList")
        self.list_widget.setSpacing(6)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Выбор только одного элемента
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Фокусироваться на списке
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding) # Разрешить растягивать список по горизонтали и вертикали
        """Добавление списка в тело панели"""
        layout.addWidget(self.list_widget, stretch=1)

    """Установка списка исполнительных механизмов"""
    def set_actuators(self, actuators: list[tuple[int, str]]) -> None:
        self.list_widget.clear() # Очистка списка
        for actuator_id, name in actuators:
            self.list_widget.addItem(f"ID: {actuator_id} {name}") # Добавление механизма в список
        self.actuators_changed.emit(actuators) # Сигнал о том, что список исполнительных механизмов изменился

    """Очистка списка исполнительных механизмов"""
    def clear_actuators(self) -> None:
        self.set_actuators([]) # Очистка списка

    """Установка доступности кнопки добавления механизмов"""
    def set_add_button_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)
