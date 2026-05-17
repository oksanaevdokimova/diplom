"""Состояние связи с контроллером."""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

"""Панель статуса связи с контроллером"""
class ConnectionStatusPanel(QFrame):
    """Конструктор панели статуса связи с контроллером"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value_labels: dict[str, QLabel] = {}
        self._build_ui() # Построение интерфейса

    """Структура панели статуса связи с контроллером"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout = QVBoxLayout(self) # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        main_layout.setSpacing(10) # Отступ между элементами по вертикали
        """Контейнер заголовка"""
        header_container = QHBoxLayout()
        self.title_label = QLabel("Состояние связи")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        main_layout.addLayout(header_container)
        """Тело панели"""
        body_container = QVBoxLayout()
        body_container.setSpacing(10)
        body_container.addLayout(self._field_row("Канал:", self._make_value_label("channel")))
        body_container.addLayout(self._status_row())
        self.last_message_label = self._make_value_label("last_message")
        body_container.addLayout(self._field_row("Последнее сообщение:", self.last_message_label))
        """Добавить тело панели в главную раскладку"""
        main_layout.addLayout(body_container)

    """Создание метки значения"""
    def _make_value_label(self, key: str, text: str = "—") -> QLabel:
        label = QLabel(text)
        self._value_labels[key] = label
        if key == "channel":
            self.channel_label = label
        return label

    """Создание строки поля"""
    def _field_row(self, caption: str, value: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        caption_label = QLabel(caption)
        caption_label.setObjectName("fieldLabel")
        row.addWidget(caption_label)
        row.addWidget(value)
        row.addStretch(1)
        return row

    """Создание строки статуса"""
    def _status_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        """Заголовок строки статуса"""
        caption_label = QLabel("Статус:")
        caption_label.setObjectName("fieldLabel")
        row.addWidget(caption_label)
        """Значение строки статуса"""
        status_value = QWidget()
        status_layout = QHBoxLayout(status_value)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        """Точка статуса"""
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setObjectName("statusDotDisconnected")
        self.status_dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        """Текст статуса"""
        self.status_label = QLabel("Отключено")
        self.status_label.setObjectName("dataValue")
        status_layout.addWidget(self.status_dot)
        """Добавить текст статуса в строку статуса"""
        status_layout.addWidget(self.status_label)
        row.addWidget(status_value)
        row.addStretch(1)
        return row
