"""Панель технической диагностики: ERR / WARN / INFO с кодом и источником."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.diagnostic_display import DiagnosticRecord


class DiagnosticPanel(QFrame):
    _COLUMNS = ("Время", "Тип", "Код", "Сообщение", "Источник")
    _MESSAGE_COLUMN = 3
    _SOURCE_COLUMN = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[tuple[str, str, str, str, str]] = []
        self._source_min_width = 0
        self._build_ui()
        self.clear_button.clicked.connect(self.clear)

    def append_record(self, record: DiagnosticRecord) -> None:
        time_text = datetime.now().strftime("%H:%M:%S")
        self._append_row(
            time_text,
            record.level,
            record.code,
            record.message,
            record.source,
        )
        self.clear_button.setEnabled(True)

    def rows(self) -> list[tuple[str, str, str, str, str]]:
        return list(self._rows)

    def restore_rows(self, rows: list[tuple[str, str, str, str, str]]) -> None:
        self.table.setRowCount(0)
        self._rows.clear()
        if not rows:
            self.clear_button.setEnabled(False)
            self._apply_empty_column_layout()
            return
        for time_text, level, code, message, source in rows:
            self._append_row(time_text, level, code, message, source)
        self.clear_button.setEnabled(True)

    def clear(self) -> None:
        self.table.setRowCount(0)
        self._rows.clear()
        self.clear_button.setEnabled(False)
        self._apply_empty_column_layout()

    def _build_ui(self) -> None:
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        header_container = QHBoxLayout()
        header_container.setSpacing(10)
        self.title_label = QLabel("Диагностика")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        header_container.addStretch(1)
        self.clear_button = QPushButton("Очистить")
        self.clear_button.setObjectName("clearLogButton")
        self.clear_button.setEnabled(False)
        header_container.addWidget(self.clear_button)
        main_layout.addLayout(header_container)

        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        self.table = QTableWidget(0, len(self._COLUMNS))
        self.table.setObjectName("diagnosticTable")
        self.table.setHorizontalHeaderLabels(self._COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_header = self.table.horizontalHeader()
        table_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.installEventFilter(self)
        self._apply_empty_column_layout()
        body_container.addWidget(self.table, stretch=1)
        main_layout.addLayout(body_container, stretch=1)

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        if watched is self.table and event.type() == QEvent.Type.Resize:
            if self.table.rowCount() > 0:
                self._apply_source_column_width()
        return super().eventFilter(watched, event)

    def _append_row(
        self,
        time_text: str,
        level: str,
        code: str,
        message: str,
        source: str,
    ) -> None:
        was_empty = self.table.rowCount() == 0
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((time_text, level, code, message, source)):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setToolTip(text)
            self.table.setItem(row, column, item)
        self._rows.append((time_text, level, code, message, source))
        if was_empty:
            self._apply_filled_column_layout()
        self._resize_columns()
        self.table.scrollToBottom()

    def _apply_empty_column_layout(self) -> None:
        """Пока записей нет: «Источник» заполняет таблицу."""
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(len(self._COLUMNS)):
            if column == self._SOURCE_COLUMN:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        for column in range(self._SOURCE_COLUMN):
            self.table.resizeColumnToContents(column)

    def _apply_filled_column_layout(self) -> None:
        """Время–сообщение по тексту; «Источник» — min по тексту, max на остаток."""
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(len(self._COLUMNS)):
            if column == self._SOURCE_COLUMN:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            else:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    def _resize_columns(self) -> None:
        if self.table.rowCount() == 0:
            return
        header = self.table.horizontalHeader()
        for column in range(self._SOURCE_COLUMN):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
            self.table.resizeColumnToContents(column)
        header.setSectionResizeMode(self._SOURCE_COLUMN, QHeaderView.ResizeMode.ResizeToContents)
        self.table.resizeColumnToContents(self._SOURCE_COLUMN)
        self._source_min_width = self.table.columnWidth(self._SOURCE_COLUMN)
        header.setSectionResizeMode(self._SOURCE_COLUMN, QHeaderView.ResizeMode.Fixed)
        self._apply_source_column_width()

    def _apply_source_column_width(self) -> None:
        if self.table.rowCount() == 0:
            return
        other_width = sum(
            self.table.columnWidth(column) for column in range(self._SOURCE_COLUMN)
        )
        viewport_width = self.table.viewport().width()
        remaining = max(0, viewport_width - other_width)
        natural_total = other_width + self._source_min_width
        if natural_total <= viewport_width:
            source_width = max(self._source_min_width, remaining)
        else:
            source_width = self._source_min_width
        self.table.setColumnWidth(self._SOURCE_COLUMN, source_width)
