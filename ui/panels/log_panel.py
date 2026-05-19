"""Панель журнала событий приложения"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


"""Панель журнала событий"""
class LogPanel(QFrame):
    _COLUMNS = ("Время", "Событие", "Описание")
    _DESCRIPTION_COLUMN = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entries: list[tuple[str, str, str]] = []
        self._build_ui()
        self.clear_button.clicked.connect(self.clear_log)
        self.save_button.clicked.connect(self.save_log_to_file)

    def _build_ui(self) -> None:
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        header_container = QHBoxLayout()
        header_container.setSpacing(10)
        self.title_label = QLabel("Журнал событий")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        header_container.addStretch(1)
        self.clear_button = QPushButton("Очистить")
        self.clear_button.setObjectName("clearLogButton")
        self.clear_button.setEnabled(False)
        self.save_button = QPushButton("Сохранить в файл")
        self.save_button.setObjectName("saveLogButton")
        self.save_button.setEnabled(False)
        header_container.addWidget(self.clear_button)
        header_container.addWidget(self.save_button)
        main_layout.addLayout(header_container)

        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        self.table = QTableWidget(0, len(self._COLUMNS))
        self.table.setObjectName("dataTable")
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
        self._apply_empty_column_layout()
        body_container.addWidget(self.table, stretch=1)
        main_layout.addLayout(body_container, stretch=1)

    def append_entry(self, event: str, description: str) -> None:
        time_text = datetime.now().strftime("%H:%M:%S")
        self._append_row(time_text, event, description)
        self._entries.append((time_text, event, description))
        self.clear_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def entries(self) -> list[tuple[str, str, str]]:
        return list(self._entries)

    def restore_entries(self, entries: list[tuple[str, str, str]]) -> None:
        self.table.setRowCount(0)
        self._entries.clear()
        if not entries:
            self.clear_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self._apply_empty_column_layout()
            return
        for time_text, event, description in entries:
            self._append_row(time_text, event, description)
            self._entries.append((time_text, event, description))
        self.clear_button.setEnabled(True)
        self.save_button.setEnabled(True)

    def clear_log(self) -> None:
        self.table.setRowCount(0)
        self._entries.clear()
        self._apply_empty_column_layout()
        self.clear_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def _suggested_export_path(self, suffix: str) -> str:
        documents = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation,
        )
        folder = Path(documents) if documents else Path.home()
        return str(folder / f"Журнал событий{suffix}")

    def save_log_to_file(self) -> None:
        if not self._entries:
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить журнал",
            self._suggested_export_path(".xlsx"),
            "Excel (*.xlsx);;Текст (*.txt);;Все файлы (*)",
        )
        if not path:
            return
        export_path = Path(path)
        if not export_path.suffix:
            if selected_filter and "txt" in selected_filter.lower():
                export_path = export_path.with_suffix(".txt")
            else:
                export_path = export_path.with_suffix(".xlsx")
        try:
            saved_path = self._write_log_export(export_path)
        except OSError as exc:
            QMessageBox.warning(self, "Сохранение журнала", f"Не удалось сохранить файл:\n{exc}")
            return
        self.append_entry(
            "Сохранение журнала",
            f"Журнал сохранён: {saved_path}",
        )

    def _write_log_export(self, path: Path) -> Path:
        if path.suffix.lower() == ".txt":
            path.write_text(self._format_txt_export(), encoding="utf-8")
            return path
        export_path = path if path.suffix.lower() == ".xlsx" else path.with_suffix(".xlsx")
        self._write_excel_export(export_path)
        return export_path

    def _format_txt_export(self) -> str:
        lines = ["\t".join(self._COLUMNS), *("\t".join(row) for row in self._entries)]
        return "\n".join(lines) + "\n"

    def _write_excel_export(self, path: Path) -> None:
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Журнал"
        sheet.append(list(self._COLUMNS))
        for row in self._entries:
            sheet.append(list(row))
        workbook.save(path)

    def _append_row(self, time_text: str, event: str, description: str) -> None:
        was_empty = self.table.rowCount() == 0
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((time_text, event, description)):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setToolTip(text)
            self.table.setItem(row, column, item)
        if was_empty:
            self._apply_filled_column_layout()
        self._resize_columns()
        self.table.scrollToBottom()

    def _apply_empty_column_layout(self) -> None:
        """Как в диагностике: «Описание» заполняет таблицу, пока записей нет."""
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        for column in range(self._DESCRIPTION_COLUMN):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(
            self._DESCRIPTION_COLUMN,
            QHeaderView.ResizeMode.Stretch,
        )
        for column in range(self._DESCRIPTION_COLUMN):
            self.table.resizeColumnToContents(column)

    def _apply_filled_column_layout(self) -> None:
        """Есть записи: все столбцы по ширине текста, при необходимости — горизонтальная прокрутка."""
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(len(self._COLUMNS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    def _resize_columns(self) -> None:
        if self.table.rowCount() == 0:
            return
        for column in range(len(self._COLUMNS)):
            self.table.resizeColumnToContents(column)
