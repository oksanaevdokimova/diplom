"""Главное окно приложения оператора"""

from __future__ import annotations
from copy import deepcopy
from datetime import datetime
from typing import Any

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from core.command_builder import build_command, build_stop_command
from core.command_manager import (
    CommandManager,
    format_command_journal_description,
    response_status_label,
)
from core import diagnostic_display as diag
from core import ui_session
from core.link_manager import LinkManager, format_channel_short, format_connection_config
from core.operation_checks import check_config_for_connect, check_telemetry_issues
from protocol.message import AppMessage
from ui.panels.actuator_list_panel import ActuatorListPanel
from ui.panels.connection_panel import ConnectionPanel
from ui.panels.connection_status_panel import ConnectionStatusPanel
from ui.panels.control_panel import ControlPanel
from ui.panels.diagnostic_panel import DiagnosticPanel
from ui.panels.log_panel import LogPanel
from ui.panels.telemetry_panel import TelemetryPanel


"""Главное окно приложения оператора"""
class MainWindow(QMainWindow):
    """Конструктор главного окна"""
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__()
        self._config = deepcopy(config) # Рабочая копия конфигурации
        self._user_disconnect_pending = False
        self._link_established = False
        self._disconnect_notified = False
        self._last_sent_command: AppMessage | None = None
        self._link = LinkManager(self._config, self) # Управление каналом связи
        self._commands = CommandManager(float(self._config.get("timeout_seconds", 60)), self) # Ожидание ответов по command_id
        self.setWindowTitle("Система управления исполнительными механизмами робота") # Заголовок окна
        screen = QGuiApplication.primaryScreen() # Основной экран для геометрии окна
        area = screen.availableGeometry() # Доступная область без док-панелей ОС
        self.setGeometry(area) # Размер и позиция под доступную область
        self.setMinimumSize(area.width(), area.height()) # Минимум не меньше начальной области
        self._build_ui() # Построение интерфейса
        self._wire_link_manager() # Связь сигналов канала и панелей
        self._apply_default_speed_from_config()
        self._restore_ui_session()

    def _apply_default_speed_from_config(self) -> None:
        speed = int(self._config.get("default_speed", 10))
        self.control_panel.set_default_speed(speed)
        self.telemetry_panel.set_default_speed(speed)

    """Структура главного окна"""
    def _build_ui(self) -> None:
        """Центральный виджет и общая вертикальная раскладка"""
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10) # Отступы содержимого от краёв окна
        layout.setSpacing(10) # Расстояние между вертикальными блоками

        """Верхний блок: панель подключения"""
        self.connection_panel = ConnectionPanel(self._config, self)
        self.connection_panel.config_saved.connect(self._on_config_saved) # Обновление локальной копии конфигурации после сохранения в файл
        layout.addWidget(self.connection_panel)

        """Средняя строка: список механизмов, управление, телеметрия и статус связи"""
        middle_row = QHBoxLayout()
        middle_row.setSpacing(10) # Расстояние между колонками средней строки
        self.actuator_list_panel = ActuatorListPanel(self)
        middle_row.addWidget(self.actuator_list_panel, 2) # Список механизмов — меньшая доля ширины
        self.control_panel = ControlPanel(self)
        middle_row.addWidget(self.control_panel, 3) # Панель управления — шире списка

        """Синхронизация выбора механизма между списком и панелью управления"""
        self.connection_panel.connection_changed.connect(self._on_connection_changed)
        self.actuator_list_panel.actuators_changed.connect(self._on_actuators_changed)
        self.actuator_list_panel.actuator_selected.connect(self._on_actuator_list_selected)
        self.control_panel.actuator_combo.currentIndexChanged.connect(self._on_control_actuator_changed)
        self._syncing_actuator_selection = False # Флаг реентрантности при синхронизации выбора

        """Правая колонка: телеметрия и состояние связи"""
        right_column_widget = QWidget()
        right_column = QVBoxLayout(right_column_widget)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(10)
        right_column.setAlignment(Qt.AlignmentFlag.AlignTop) # Прижать содержимое колонки к верху
        self.telemetry_panel = TelemetryPanel(self)
        right_column.addWidget(self.telemetry_panel)
        self.connection_status_panel = ConnectionStatusPanel(self)
        right_column.addWidget(self.connection_status_panel)
        right_column.addStretch(1) # Заполнитель снизу, если есть свободная высота
        middle_row.addWidget(right_column_widget, 3)
        layout.addLayout(middle_row, stretch=1) # Средняя строка забирает основную высоту

        """Нижняя строка: диагностика и журнал"""
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        self.diagnostic_panel = DiagnosticPanel(self)
        self.log_panel = LogPanel(self)
        bottom_row.addWidget(self.diagnostic_panel, 1)
        bottom_row.addWidget(self.log_panel, 1)
        layout.addLayout(bottom_row, stretch=1)

        self.setCentralWidget(central_widget)
        self._reset_connection_status_panel()
        self._refresh_operation_state()

    """Подключение сигналов канала связи и менеджера команд"""
    def _wire_link_manager(self) -> None:
        self.connection_panel.connect_requested.connect(self._on_connect_requested) # Запуск connect из UI
        self.connection_panel.connect_fields_invalid.connect(
            self._on_connection_fields_invalid,
        )
        self.connection_panel.disconnect_requested.connect(self._on_disconnect_requested)
        self.control_panel.command_send_requested.connect(self._on_command_send_requested)
        self.control_panel.input_validation_failed.connect(self._on_input_validation_failed)
        self.control_panel.stop_command_requested.connect(self._on_stop_command_requested)
        self._link.link_ready.connect(self._on_link_ready) # Успешный pong после подключения
        self._link.link_failed.connect(self._on_link_failed)
        self._link.command_link_ok.connect(self._on_command_link_ok) # pong после отправки команды
        self._link.command_failed.connect(self._on_command_failed)
        self._link.transport_disconnected.connect(self._on_transport_disconnected)
        self._link.valid_message_received.connect(self._on_valid_message_received) # Обновление «последнее сообщение»
        self._link.response_received.connect(self._commands.handle_response) # Сопоставление ответа с command_id
        self._commands.command_accepted.connect(self._on_command_accepted)
        self._commands.command_rejected.connect(self._on_command_rejected)
        self._commands.command_error.connect(self._on_command_error)
        self._commands.response_timeout.connect(self._on_command_response_timeout)
        self._link.telemetry_received.connect(self._on_telemetry_received)
        self._link.diagnostic_received.connect(self._on_diagnostic_received)
        self._link.parse_error.connect(self._on_parse_error)
        self._link.actuators_loaded.connect(self._on_actuators_loaded_from_controller)
        self._link.actuators_failed.connect(self._on_actuators_load_failed)
        self._commands.orphan_response.connect(self._on_orphan_response)

    """Сброс панели «Состояние связи» в начальное отображение"""
    def _reset_connection_status_panel(self) -> None:
        self.connection_status_panel.set_channel("")
        self.connection_status_panel.set_link_status(connected=False, text="Отключено")
        self.connection_status_panel.set_last_message("")

    def _refresh_operation_state(self) -> None:
        self.control_panel.refresh_command_buttons()

    def _append_diag(self, record: diag.DiagnosticRecord) -> None:
        self.diagnostic_panel.append_record(record)

    def _restore_ui_session(self) -> None:
        self.log_panel.restore_entries(ui_session.load_log_entries())
        self.diagnostic_panel.restore_rows(ui_session.load_diagnostic_rows())

    def _save_ui_session(self) -> None:
        ui_session.save_log_entries(self.log_panel.entries())
        ui_session.save_diagnostic_rows(self.diagnostic_panel.rows())

    def _on_connection_fields_invalid(self, issues: list) -> None:
        for issue in issues:
            self.log_panel.append_entry("Предупреждение", f"Неверное значение: {issue}")
            self._append_diag(diag.record_field_value_warning(str(issue)))
        summary = "; ".join(str(i) for i in issues)
        self.log_panel.append_entry(
            "Ошибка подключения",
            "Подключение не выполнено: исправьте параметры канала связи",
        )
        self._append_diag(diag.record_connection_failed(summary))

    def _on_input_validation_failed(self, issues: list) -> None:
        for issue in issues:
            self.log_panel.append_entry("Предупреждение", f"Неверное значение: {issue}")
            self._append_diag(diag.record_input_field_invalid(str(issue)))
        self.log_panel.append_entry(
            "Ошибка отправки",
            "Команда не отправлена: исправьте поля управления",
        )
        self._append_diag(
            diag.record_command_build_failed(),
        )

    def _notify_disconnect_from_controller(self, *, user_initiated: bool = False) -> None:
        if self._disconnect_notified or (self._user_disconnect_pending and not user_initiated):
            return
        if not self._link_established:
            return
        self._disconnect_notified = True
        self._append_diag(
            diag.record_disconnected_from_controller(user_initiated=user_initiated),
        )
        self.log_panel.append_entry(
            "Отключено",
            f"Связь с контроллером потеряна ({format_connection_config(self._config)})",
        )

    """Обработка запроса отключения от панели подключения"""
    def _on_disconnect_requested(self) -> None:
        self.log_panel.append_entry(
            "Отключение",
            f"Запрос отключения от контроллера ({format_connection_config(self._config)})",
        )
        was_connected = self._link.is_connected
        self._user_disconnect_pending = was_connected
        self._link.disconnect()
        if not was_connected:
            self._user_disconnect_pending = False

    """Обработка запроса подключения: обновление таймаутов и запуск канала"""
    def _on_connect_requested(self, config: dict[str, Any]) -> None:
        self._config = deepcopy(config)
        ok, check_text = check_config_for_connect(self._config)
        self._refresh_operation_state()
        if not ok:
            self.log_panel.append_entry("Ошибка связи", check_text)
            self._append_diag(diag.record_config_rejected(check_text))
            return
        timeout = float(self._config.get("timeout_seconds", 60))
        self._commands.set_timeout_seconds(timeout)
        channel = format_channel_short(config)
        self.connection_status_panel.set_channel(channel)
        self.connection_status_panel.set_link_status(connected=False, text="Подключение...")
        self.connection_status_panel.set_last_message("")
        self._append_diag(diag.record_link_connecting())
        self.log_panel.append_entry(
            "Подключение",
            f"Запрос подключения к контроллеру ({format_connection_config(config)})",
        )
        self._link.connect(config)

    """Канал установлен (получен pong): обновление UI и запрос списка механизмов"""
    def _on_link_ready(self) -> None:
        self._link_established = True
        self._disconnect_notified = False
        self.connection_panel.show_connected()
        self.connection_status_panel.set_link_status(connected=True, text="Подключено")
        self._refresh_operation_state()
        self._append_diag(diag.record_link_ready())
        self.log_panel.append_entry(
            "Подключено",
            f"Успешное подключение к контроллеру ({format_connection_config(self._config)})",
        )
        self.log_panel.append_entry("Запрос механизмов", "Запрос списка исполнительных механизмов")

    """Получен непустой или пустой список механизмов от контроллера"""
    def _on_actuators_loaded_from_controller(self, actuators: list) -> None:
        self.actuator_list_panel.set_actuators(actuators)
        self._append_diag(diag.record_actuators_loaded(len(actuators)))
        self._refresh_operation_state()
        self.log_panel.append_entry(
            "Механизмы",
            f"Получено исполнительных механизмов: {len(actuators)}",
        )
        if not actuators:
            self._append_diag(diag.record_actuators_empty())
            self.log_panel.append_entry(
                "Телеметрия",
                "Проверка: контроллер вернул пустой список — команды недоступны",
            )

    """Ошибка при загрузке списка механизмов"""
    def _on_actuators_load_failed(self, message: str) -> None:
        self._append_diag(diag.record_from_failure_text(message, default_source="ActuatorManager"))
        self.log_panel.append_entry("Механизмы", message)

    """Ошибка установления связи или потери канала до готовности"""
    def _on_link_failed(self, message: str) -> None:
        self._notify_disconnect_from_controller()
        was_established = self._link_established
        self._link_established = False
        self._last_sent_command = None
        self._commands.clear()
        self.connection_panel.show_disconnected()
        self._reset_connection_status_panel()
        self.connection_status_panel.set_link_status(connected=False, text="Ошибка")
        self.connection_status_panel.set_last_message(message)
        self._refresh_operation_state()
        self._append_diag(diag.record_from_failure_text(message))
        if was_established:
            self.log_panel.append_entry(
                "Ошибка связи",
                f"Потеря связи с контроллером ({format_connection_config(self._config)})",
            )
        else:
            self.log_panel.append_entry(
                "Ошибка связи",
                f"Не удалось подключиться к контроллеру ({format_connection_config(self._config)})",
            )

    """Закрытие транспорта со стороны канала или приложения"""
    def _on_transport_disconnected(self) -> None:
        user_initiated = self._user_disconnect_pending
        self._notify_disconnect_from_controller(user_initiated=user_initiated)
        self._link_established = False
        self._last_sent_command = None
        self._commands.clear()
        self.telemetry_panel.clear()
        self.connection_panel.show_disconnected()
        self._reset_connection_status_panel()
        if user_initiated:
            self._user_disconnect_pending = False
            self.log_panel.append_entry(
                "Отключено",
                f"Успешное отключение от контроллера ({format_connection_config(self._config)})",
            )

    """Отправка команды остановки выбранного механизма"""
    def _on_stop_command_requested(self) -> None:
        if not self._link.is_connected:
            hint = self.control_panel.stop_hint_text()
            self.log_panel.append_entry("Ошибка связи", hint)
            self._append_diag(diag.record_command_blocked_no_link())
            self._refresh_operation_state()
            return
        command = build_stop_command(self.control_panel)
        self._log_command_send(command)
        self._commands.register_sent(command)
        self._show_command_sending()
        self._link.send_command(command)

    """Отправка команды перемещения или остановки из полей панели управления"""
    def _on_command_send_requested(self) -> None:
        if not self._link.is_connected:
            self.log_panel.append_entry("Ошибка связи", self.control_panel.send_hint_text())
            self._append_diag(diag.record_command_blocked_no_link())
            self._refresh_operation_state()
            return
        command = build_command(
            self.control_panel,
            default_speed=int(self._config["default_speed"]),
        )
        if command is None:
            self.log_panel.append_entry(
                "Ошибка отправки",
                "Не удалось собрать команду: проверьте механизм, действие и поля",
            )
            self._append_diag(diag.record_command_build_failed())
            self._refresh_operation_state()
            return
        self._log_command_send(command)
        self._commands.register_sent(command)
        self._show_command_sending()
        self._link.send_command(command)

    """Подпись механизма из списка панели управления"""
    def _actuator_label(self, actuator_id: int | None) -> str:
        if actuator_id is None:
            return "—"
        combo = self.control_panel.actuator_combo
        index = combo.findData(actuator_id)
        if index >= 0:
            return combo.itemText(index)
        return f"ID {actuator_id}"

    """Запись в журнал об отправке команды"""
    def _log_command_send(self, command: AppMessage) -> None:
        self._last_sent_command = command
        label = self._actuator_label(command.actuator_id)
        self.log_panel.append_entry(
            "Отправка команды",
            format_command_journal_description("Отправка команды", command, label),
        )

    """Запись в журнал о принятии команды контроллером"""
    def _log_command_accepted(self) -> None:
        command = self._last_sent_command
        if command is None:
            return
        label = self._actuator_label(command.actuator_id)
        self.log_panel.append_entry(
            "Команда принята",
            format_command_journal_description("Команда принята", command, label),
        )
        self._last_sent_command = None

    """Запись в журнал об ошибке отправки команды"""
    def _log_command_send_error(self, command: AppMessage | None = None) -> None:
        cmd = command if command is not None else self._last_sent_command
        if cmd is not None:
            label = self._actuator_label(cmd.actuator_id)
            description = format_command_journal_description(
                "Не удалось отправить команду", cmd, label
            )
        else:
            actuator_id = self.control_panel.actuator_combo.currentData()
            label = self._actuator_label(actuator_id)
            description = f"Не удалось отправить команду, механизм {label}"
        self.log_panel.append_entry("Ошибка отправки", description)
        self._last_sent_command = None

    """Время для метки статуса команды"""
    def _now_hms(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    """Статус: команда ушла в канал, ожидается подтверждение доставки (pong)"""
    def _show_command_sending(self) -> None:
        self.control_panel.set_last_command_status(
            "Отправка команды",
            self._now_hms(),
            dot_object_name="statusDotDisconnected",
        )

    """Команда дошла до канала (есть pong после отправки)"""
    def _on_command_link_ok(self) -> None:
        now = self._now_hms()
        self.control_panel.set_last_command_status(
            "Команда отправлена",
            now,
            dot_object_name="statusDotConnected",
        )

    """Команда не доставлена на канал (нет pong в срок)"""
    def _on_command_failed(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log_command_send_error()
        self._commands.clear()
        self._append_diag(diag.record_from_failure_text(message, default_source="LinkWatchdog"))
        self.control_panel.set_last_command_status("Не доставлено", now, dot_object_name="statusDotDisconnected")

    """Контроллер принял или завершил команду (accepted/completed)"""
    def _on_command_accepted(self, message: AppMessage) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        label = response_status_label(message.status)
        self._log_command_accepted()
        self._append_diag(diag.record_from_response(message))
        self.control_panel.set_last_command_status(label, now, dot_object_name="statusDotConnected")

    """Контроллер отклонил команду"""
    def _on_command_rejected(self, message: AppMessage) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log_command_send_error()
        self._append_diag(diag.record_from_response(message))
        self.control_panel.set_last_command_status("Отклонено", now, dot_object_name="statusDotDisconnected")

    """Ответ контроллера со статусом error"""
    def _on_command_error(self, message: AppMessage) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log_command_send_error()
        self._append_diag(diag.record_from_response(message))
        self.control_panel.set_last_command_status("Ошибка", now, dot_object_name="statusDotDisconnected")

    """Ответ пришёл, но ожидающей команды уже нет"""
    def _on_orphan_response(self, message: AppMessage) -> None:
        self._log_command_send_error()
        self._append_diag(diag.record_orphan_response(message))

    """Истёк таймаут ожидания ответа на команду"""
    def _on_command_response_timeout(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log_command_send_error()
        self._append_diag(diag.record_from_failure_text(message, default_source="CommandManager"))
        self.control_panel.set_last_command_status("Нет ответа", now, dot_object_name="statusDotDisconnected")

    """Любое корректно разобранное входящее сообщение — обновление времени последнего сообщения"""
    def _on_valid_message_received(self, _message: object) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.connection_status_panel.set_last_message(now)

    """Список механизмов изменился (из контроллера или UI): синхронизация с панелью управления"""
    def _on_actuators_changed(self, actuators: list[tuple[int, str]]) -> None:
        selected = self.actuator_list_panel.selected_actuator()
        select_id = selected[0] if selected is not None else None
        self.control_panel.set_actuators(actuators, select_id=select_id)
        if selected is None and actuators:
            selected = actuators[0]
            self.actuator_list_panel.select_actuator(selected[0], emit_signal=False)
        if selected is not None:
            self._apply_actuator_selection(*selected, source="list")
            return
        self.telemetry_panel.set_selected_actuator(None)

    """Выбор строки в списке механизмов"""
    def _on_actuator_list_selected(self, actuator_id: int, name: str) -> None:
        self._apply_actuator_selection(actuator_id, name, source="list")

    """Смена механизма в выпадающем списке панели управления"""
    def _on_control_actuator_changed(self) -> None:
        if self._syncing_actuator_selection:
            return
        selected = self.control_panel.selected_actuator()
        if selected is None:
            self.telemetry_panel.set_selected_actuator(None)
            return
        self._apply_actuator_selection(*selected, source="control")

    """Единая точка применения выбора механизма к списку, комбо и боковым панелям"""
    def _apply_actuator_selection(self, actuator_id: int, name: str, *, source: str) -> None:
        if self._syncing_actuator_selection:
            return
        self._syncing_actuator_selection = True
        try:
            if source != "control":
                self.control_panel.select_actuator(actuator_id, emit_signal=False)
            if source != "list":
                self.actuator_list_panel.select_actuator(actuator_id, emit_signal=False)
            self.telemetry_panel.set_selected_actuator(actuator_id, name=name)
            self._refresh_operation_state()
        finally:
            self._syncing_actuator_selection = False

    """Обновление телеметрии для текущего выбора"""
    def _on_telemetry_received(self, message: AppMessage) -> None:
        issues = check_telemetry_issues(message)
        if issues:
            self._append_diag(diag.record_telemetry_validation(issues, message))
        selected = self.control_panel.selected_actuator()
        if (
            issues
            and selected is not None
            and message.actuator_id is not None
            and int(message.actuator_id) == selected[0]
        ):
            self.log_panel.append_entry(
                "Телеметрия",
                f"Проверка механизма {message.actuator_id}: {'; '.join(issues)}",
            )
        self.telemetry_panel.update_from_message(message)

    """Техническое сообщение diagnostic от контроллера"""
    def _on_diagnostic_received(self, message: AppMessage) -> None:
        self._append_diag(diag.record_from_controller_diagnostic(message))

    """Ошибка разбора входящего JSON / протокола"""
    def _on_parse_error(self, detail: str) -> None:
        self._append_diag(diag.record_from_parse_detail(detail))

    """Изменение флага соединения с панели подключения"""
    def _on_connection_changed(self, connected: bool) -> None:
        self.control_panel.set_link_connected(connected)
        if not connected:
            self.actuator_list_panel.clear_actuators()
            self.telemetry_panel.clear()
        self._refresh_operation_state()

    """Конфигурация сохранена из панели подключения"""
    def _on_config_saved(self, config: dict[str, Any]) -> None:
        self._config = deepcopy(config)
        self._apply_default_speed_from_config()
        self._refresh_operation_state()

    """Текущая конфигурация приложения (после слияния и сохранений)"""
    def config(self) -> dict[str, Any]:
        return self._config

    """Закрытие окна: сохранить журнал и диагностику, отключить транспорт"""
    def closeEvent(self, event: QEvent) -> None:
        self._save_ui_session()
        self._link.disconnect()
        event.accept()

    """Выход из полноэкранного режима по Escape"""
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
            return
        super().keyPressEvent(event)
