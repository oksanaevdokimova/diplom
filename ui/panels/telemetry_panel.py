"""Телеметрия выбранного механизма"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.telemetry_display import (
    TELEMETRY_ROW_DEFS,
    build_telemetry_rows,
    format_mechanism_display,
)
from protocol.message import AppMessage


"""Кэш последних телеметрических сообщений по механизмам"""
class ActuatorTelemetryCache:
    def __init__(self) -> None:
        self._by_actuator: dict[int, AppMessage] = {}
        self._selected_actuator_id: int | None = None
        self._selected_actuator_name: str | None = None

    def update_from_message(self, message: AppMessage) -> bool:
        if message.actuator_id is None:
            return False
        actuator_id = int(message.actuator_id)
        self._by_actuator[actuator_id] = message
        return actuator_id == self._selected_actuator_id

    def set_selected_actuator(self, actuator_id: int | None, *, name: str | None = None) -> None:
        self._selected_actuator_id = actuator_id
        self._selected_actuator_name = name

    def clear(self) -> None:
        self._by_actuator.clear()
        self._selected_actuator_id = None
        self._selected_actuator_name = None

    def selected_message(self) -> AppMessage | None:
        if self._selected_actuator_id is None:
            return None
        return self._by_actuator.get(self._selected_actuator_id)

    @property
    def selected_actuator_name(self) -> str | None:
        return self._selected_actuator_name

    @property
    def selected_actuator_id(self) -> int | None:
        return self._selected_actuator_id


"""Панель телеметрии выбранного механизма"""
class TelemetryPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value_labels: dict[str, QLabel] = {}
        self._cache = ActuatorTelemetryCache()
        self._default_speed: int | None = None
        self._build_ui()

    def set_default_speed(self, value: int) -> None:
        self._default_speed = value
        self._refresh_display()

    def update_from_message(self, message: AppMessage) -> None:
        if self._cache.update_from_message(message):
            self._refresh_display()

    def set_selected_actuator(self, actuator_id: int | None, *, name: str | None = None) -> None:
        self._cache.set_selected_actuator(actuator_id, name=name)
        self._refresh_display()

    def clear(self) -> None:
        self._cache.clear()
        self._refresh_display()

    def _refresh_display(self) -> None:
        actuator_id = self._cache.selected_actuator_id
        mechanism = format_mechanism_display(actuator_id, self._cache.selected_actuator_name)
        rows = build_telemetry_rows(
            self._cache.selected_message(),
            mechanism_name=mechanism,
            actuator_id=actuator_id,
            default_speed=self._default_speed,
        )
        for row in rows:
            self._value_labels[row.key].setText(row.value)

    def _build_ui(self) -> None:
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        header_container = QHBoxLayout()
        self.title_label = QLabel("Телеметрия")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(
            self.title_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        main_layout.addLayout(header_container)

        body_container = QVBoxLayout()
        body_container.setSpacing(0)
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        self._caption_labels: dict[str, QLabel] = {}
        for row_index, (key, caption) in enumerate(TELEMETRY_ROW_DEFS):
            caption_label = QLabel(caption)
            caption_label.setObjectName("fieldLabel")
            self._caption_labels[key] = caption_label
            grid.addWidget(caption_label, row_index, 0, Qt.AlignmentFlag.AlignTop)

            value = QLabel("")
            value.setObjectName("dataValue")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._value_labels[key] = value
            grid.addWidget(value, row_index, 1, Qt.AlignmentFlag.AlignTop)

        body_container.addLayout(grid)
        main_layout.addLayout(body_container, stretch=1)
