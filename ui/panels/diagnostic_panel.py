"""Диагностические сообщения от контроллера."""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

"""Панель диагностики"""
class DiagnosticPanel(QFrame):
    _COLUMNS = ("Время", "Уровень", "Код", "Описание")
    _COMPACT_COLUMN_WIDTH = 110
    """Конструктор панели диагностики"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()  # Построение интерфейса

    """Структура панели диагностики"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)  # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0)  # Чтобы не было лишних отступов
        main_layout.setSpacing(10)  # Отступ между элементами по вертикали

        """Контейнер заголовка"""
        header_container = QHBoxLayout()
        self.title_label = QLabel("Диагностика")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        """Добавить контейнер заголовка в тело панели"""
        main_layout.addLayout(header_container)

        """Тело панели"""
        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        """Таблица для диагностических сообщений"""
        self.table = QTableWidget(0, len(self._COLUMNS))
        self.table.setObjectName("dataTable")
        self.table.setHorizontalHeaderLabels(self._COLUMNS) # Установить заголовки колонок
        self.table.verticalHeader().setVisible(False) # Скрыть вертикальную заголовковую строку
        self.table.setShowGrid(True) # Показать сетку
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Запретить редактирование ячеек
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Выделение строк
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) # Выделение одной строки
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Разрешить растягивать таблицу по высоте
        table_header = self.table.horizontalHeader()
        table_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table_header.setStretchLastSection(True)
        for column in range(3):
            table_header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed) # Фиксированная ширина колонок
            table_header.resizeSection(column, self._COMPACT_COLUMN_WIDTH) # Установить ширину колонок
        table_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        """Добавить таблицу в тело панели"""
        body_container.addWidget(self.table, stretch=1)
        """Добавить тело панели в главную раскладку"""
        main_layout.addLayout(body_container, stretch=1)
