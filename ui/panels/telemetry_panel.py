"""Телеметрия выбранного механизма"""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

"""Панель телеметрии выбранного механизма"""
class TelemetryPanel(QFrame):
    """Конструктор панели телеметрии выбранного механизма"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value_labels: dict[str, QLabel] = {}
        self._build_ui() # Построение интерфейса

    """Структура панели телеметрии"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout = QVBoxLayout(self) # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        main_layout.setSpacing(10) # Отступ между элементами по вертикали
        """Контейнер заголовка"""
        header_container = QHBoxLayout()
        self.title_label = QLabel("Телеметрия")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        main_layout.addLayout(header_container)
        """Тело панели"""
        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        """Сетка для расположения элементов панели"""
        grid = QGridLayout()
        grid.setHorizontalSpacing(10) # Отступ между элементами в горизонтальном направлении
        grid.setVerticalSpacing(10) # Отступ между элементами в вертикальном направлении
        grid.setColumnStretch(1, 1) # Разрешить растягивать вторую колонку на всю ширину панели
        """Элементы панели"""
        rows = (
            ("mechanism", "Механизм:", "—"),
            ("position", "Положение:", "—"),
            ("speed", "Скорость:", "—"),
            ("direction", "Направление:", "—"),
            ("state", "Состояние:", "—"),
            ("error_state", "Ошибка:", "—"),
        )
        for row_index, (key, caption, default) in enumerate(rows): # Цикл по строкам сетки
            caption_label = QLabel(caption)
            caption_label.setObjectName("fieldLabel") # Установить название класса для заголовка
            grid.addWidget(caption_label, row_index, 0) # Добавить заголовок в первую колонку
            value = QLabel(default) # Значение
            self._value_labels[key] = value # Сохранить значение в словаре
            grid.addWidget(value, row_index, 1) # Добавить значение во вторую колонку
        """Добавить сетку в тело панели"""
        body_container.addLayout(grid)
        main_layout.addLayout(body_container)
