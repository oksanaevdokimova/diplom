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
    QListWidgetItem,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

_PLUS_ICON = Path(__file__).resolve().parent.parent / "styles" / "icons" / "plus.svg"

_NAME_ROLE = Qt.ItemDataRole.UserRole + 1

"""Панель списка исполнительных механизмов"""
class ActuatorListPanel(QFrame):
    actuators_changed = Signal(list)
    actuator_selected = Signal(int, str)

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
        self.add_button.setVisible(False)
        header_container.addWidget(self.add_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        """Добавление контейнера заголовка в тело панели"""
        layout.addLayout(header_container)

        """Список исполнительных механизмов"""
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("actuatorList")
        self.list_widget.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.list_widget.viewport().setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Выбор только одного элемента
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Фокусироваться на списке
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding) # Разрешить растягивать список по горизонтали и вертикали
        self.list_widget.currentRowChanged.connect(self._on_current_row_changed)
        """Добавление списка в тело панели"""
        layout.addWidget(self.list_widget, stretch=1)

    """Текущий выбранный механизм или None"""
    def selected_actuator(self) -> tuple[int, str] | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        actuator_id = item.data(Qt.ItemDataRole.UserRole)
        name = item.data(_NAME_ROLE)
        if actuator_id is None or name is None:
            return None
        return int(actuator_id), str(name)

    """Выделить механизм по id; emit_signal=False при программной синхронизации"""
    def select_actuator(self, actuator_id: int, *, emit_signal: bool = True) -> bool:
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == actuator_id:
                previous = self.list_widget.blockSignals(not emit_signal)
                self.list_widget.setCurrentRow(row)
                self.list_widget.blockSignals(previous)
                return True
        return False

    """Реакция на смену текущей строки списка"""
    def _on_current_row_changed(self, row: int) -> None:
        if row < 0:
            return
        selected = self.selected_actuator()
        if selected is not None:
            self.actuator_selected.emit(*selected)

    """Установка списка исполнительных механизмов"""
    def set_actuators(self, actuators: list[tuple[int, str]]) -> None:
        previous_id = self.selected_actuator()
        previous_id = previous_id[0] if previous_id is not None else None
        self.list_widget.blockSignals(True)
        try:
            self.list_widget.clear()
            for actuator_id, name in actuators:
                item = QListWidgetItem(f"ID: {actuator_id} {name}")
                item.setData(Qt.ItemDataRole.UserRole, actuator_id)
                item.setData(_NAME_ROLE, name)
                self.list_widget.addItem(item)
            if actuators:
                keep_id = previous_id if previous_id in {aid for aid, _ in actuators} else actuators[0][0]
                self.select_actuator(keep_id, emit_signal=False)
        finally:
            self.list_widget.blockSignals(False)
        self.actuators_changed.emit(actuators)

    """Очистка списка исполнительных механизмов"""
    def clear_actuators(self) -> None:
        self.set_actuators([]) # Очистка списка

