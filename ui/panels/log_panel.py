"""Журнал событий приложения."""

from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


"""Панель журнала событий"""
class LogPanel(QFrame):
    _COLUMNS = ("Время", "Событие", "Описание")
    _COMPACT_COLUMN_WIDTH = 110
    _DATETIME_COLUMN_WIDTH = 140

    """Конструктор панели журнала событий"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()  # Построение интерфейса

    """Структура панели журнала событий"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)  # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0)  # Чтобы не было лишних отступов
        main_layout.setSpacing(10)  # Отступ между элементами по вертикали

        """Контейнер заголовка"""
        header_container = QHBoxLayout()
        header_container.setSpacing(10)
        """Заголовок панели"""
        self.title_label = QLabel("Журнал событий")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        header_container.addStretch(1)
        """Кнопка очистки журнала"""
        self.clear_button = QPushButton("Очистить")
        self.clear_button.setObjectName("clearLogButton")
        self.clear_button.setEnabled(False)
        """Кнопка сохранения журнала в файл"""
        self.save_button = QPushButton("Сохранить в файл")
        self.save_button.setObjectName("saveLogButton")
        self.save_button.setEnabled(False)
        """Добавить кнопки в контейнер заголовка"""
        header_container.addWidget(self.clear_button)
        header_container.addWidget(self.save_button)
        """Добавить контейнер заголовка в тело панели"""
        main_layout.addLayout(header_container)

        """Тело панели"""
        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        """Таблица журнала событий"""
        self.table = QTableWidget(0, len(self._COLUMNS))
        self.table.setObjectName("dataTable")
        self.table.setHorizontalHeaderLabels(self._COLUMNS) # Установить заголовки колонок
        self.table.verticalHeader().setVisible(False) # Скрыть вертикальную заголовковую строку
        self.table.setShowGrid(True) # Показать сетку
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Запретить редактирование ячеек
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows) # Выделение строк
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection) # Выделение одной строки
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Разрешить растягивать таблицу по высоте
        """Заголовок таблицы"""
        table_header = self.table.horizontalHeader()
        table_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table_header.setStretchLastSection(True)
        table_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table_header.resizeSection(0, self._DATETIME_COLUMN_WIDTH)
        table_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        table_header.resizeSection(1, self._COMPACT_COLUMN_WIDTH)
        table_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        """Добавить таблицу в тело панели"""
        body_container.addWidget(self.table, stretch=1)
        """Добавить тело панели в главную раскладку"""
        main_layout.addLayout(body_container, stretch=1)
