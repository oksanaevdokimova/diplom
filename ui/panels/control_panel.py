"""Панель управления выбранным механизмом"""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.operation_checks import explain_send_blocked, explain_stop_blocked

_ERROR_SLOT_HEIGHT = 20

"""Надпись + поле ввода/выбора"""
class ControlFieldGroup(QWidget):
    """Конструктор надписи + поля ввода/выбора"""
    def __init__(
        self,
        label_text: str,
        control: QWidget,
        width: int,
        panel: ControlPanel,
        *,
        suffix: str | None = None,
        expand: bool = False,
        reserve_error_slot: bool = False,
    ) -> None:
        super().__init__()
        """Контейнер для группы надписи + поля ввода/выбора"""
        field_group_grid = QGridLayout(self)
        field_group_grid.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        field_group_grid.setHorizontalSpacing(10) # Отступ между надписью и полем ввода/выбора
        field_group_grid.setVerticalSpacing(0)
        """Надпись"""
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        """Поле ввода/выбора"""
        control.setFixedHeight(35) # Высота поля ввода/выбора
        if expand:
            control.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Разрешить растягивать группу надписи + поля ввода/выбора по горизонтали и вертикали
            field_group_grid.setColumnStretch(0, 0) # Не растягивать первый столбец
            field_group_grid.setColumnStretch(1, 1) # Растягивать второй столбец
        else:
            control.setFixedWidth(width)
            control.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Фиксированная ширина и высота поля ввода/выбора
            field_group_grid.setColumnStretch(0, 0) # Не растягивать первый столбец
            field_group_grid.setColumnStretch(1, 0) # Не растягивать второй столбец
        self.error_label: QLabel | None = None
        row_align = Qt.AlignmentFlag.AlignVCenter
        field_group_grid.addWidget(label, 0, 0, row_align)
        """Поле ввода/выбора с суффиксом"""
        if suffix:
            control_cell = QWidget()
            if expand: # Разрешить растягивать поле ввода/выбора с суффиксом по горизонтали и вертикали
                control_cell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            control_row = QHBoxLayout(control_cell) # Горизонтальная раскладка для поля ввода/выбора с суффиксом
            control_row.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
            control_row.setSpacing(6) # Отступ между элементами по горизонтали
            suffix_label = QLabel(suffix) # Надпись с суффиксом
            if expand:
                control_row.addWidget(control, 1, row_align)
            else:
                control_row.addWidget(control, 0, row_align)
            control_row.addWidget(suffix_label, alignment=row_align)
            if not expand:
                control_row.addStretch(1) # Разрешить растягивать поле ввода/выбора с суффиксом по вертикали
            field_group_grid.addWidget(control_cell, 0, 1, row_align)
        else:
            field_group_grid.addWidget(control, 0, 1, row_align)

        if reserve_error_slot:
            field_group_grid.setRowMinimumHeight(0, 35)
            field_group_grid.setRowMinimumHeight(1, _ERROR_SLOT_HEIGHT)
            self.error_label = QLabel("")
            self.error_label.setObjectName("fieldError")
            self.error_label.setWordWrap(False)
            self.error_label.setFixedHeight(_ERROR_SLOT_HEIGHT)
            self.error_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.error_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            field_group_grid.addWidget(
                self.error_label, 1, 0, 1, 2, Qt.AlignmentFlag.AlignTop,
            )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding if expand else QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed if reserve_error_slot else QSizePolicy.Policy.Preferred,
        )
        if isinstance(control, QLineEdit) and self.error_label is not None:
            control.textChanged.connect(lambda: panel._clear_error(control))
            panel._field_error_labels[control] = self.error_label

"""Панель управления выбранным механизмом"""
class ControlPanel(QFrame):
    command_send_requested = Signal() # Сигнал отправки команды
    stop_command_requested = Signal() # Сигнал остановки команды
    input_validation_failed = Signal(list) # Некорректные поля при отправке команды

    """Конструктор панели управления выбранным механизмом"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._field_error_labels: dict[QLineEdit, QLabel] = {}
        self._link_connected = False # Флаг соединения с контроллером
        self._build_ui() # Построение интерфейса

    """Структура панели управления выбранным механизмом"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Разрешить растягивать панель по горизонтали и вертикали
        main_layout = QVBoxLayout(self) # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        main_layout.setSpacing(10) # Установка отступа между элементами по вертикали

        """Контейнер заголовка"""
        header_container = QHBoxLayout()
        """Название панели"""
        self.title_label = QLabel("Панель управления")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        """Добавление контейнера заголовка в тело панели"""
        main_layout.addLayout(header_container)

        """Контейнер для надписей + полей ввода/выбора"""
        fields_container = QVBoxLayout() # Контейнер: надписи + поля ввода/выбора
        fields_container.setSpacing(10) # Отступ между элементами по вертикали
        """Список механизмов"""
        self.actuator_combo = self._create_combo() # Создание выпадающего списка для выбора механизма
        self.actuator_combo.currentIndexChanged.connect(self.refresh_command_buttons)
        fields_container.addWidget(ControlFieldGroup("Механизм:", self.actuator_combo, 0, self, expand=True))
        """Список действий"""
        self.action_combo = self._create_combo() # Создание выпадающего списка для выбора действия
        self.action_combo.addItem("Перемещение", "move")
        self.action_combo.addItem("Остановка", "stop")
        self.action_combo.setEnabled(False)
        self.action_combo.currentIndexChanged.connect(self._update_motion_fields_enabled)
        self.action_combo.currentIndexChanged.connect(self.refresh_command_buttons)
        fields_container.addWidget(ControlFieldGroup("Действие:", self.action_combo, 0, self, expand=True))
        """Список направлений"""
        self.direction_combo = self._create_combo() # Создание выпадающего списка для выбора направления
        self.direction_combo.addItem("Вперёд", "forward")
        self.direction_combo.addItem("Назад", "backward")
        self.direction_combo.setEnabled(False)
        fields_container.addWidget(ControlFieldGroup("Направление:", self.direction_combo, 0, self, expand=True))
        """Список параметров"""
        params_row = QHBoxLayout() # Горизонтальная раскладка для параметров
        params_row.setSpacing(10) # Отступ между элементами по горизонтали
        self.position_edit = QLineEdit() # Поле ввода для положения
        self.position_edit.setEnabled(False)
        self.position_edit.editingFinished.connect(self._on_position_editing_finished)
        params_top = Qt.AlignmentFlag.AlignTop
        params_row.addWidget(
            ControlFieldGroup(
                "Положение:", self.position_edit, 0, self,
                suffix="шаг.", expand=True, reserve_error_slot=True,
            ),
            1,
            params_top,
        )
        self.speed_edit = QLineEdit() # Поле ввода для скорости
        self.speed_edit.setEnabled(False)
        self.speed_edit.editingFinished.connect(self._on_speed_editing_finished)
        params_row.addWidget(
            ControlFieldGroup(
                "Скорость:", self.speed_edit, 0, self,
                suffix="шаг./с", expand=True, reserve_error_slot=True,
            ),
            1,
            params_top,
        )
        fields_container.addLayout(params_row)
        """Добавление контейнера для надписей + полей ввода/выбора в тело панели"""
        main_layout.addLayout(fields_container)
        """Контейнер кнопок и статуса последней команды"""
        actions_container = QVBoxLayout()
        actions_container.setSpacing(10) # Отступ между элементами по вертикали
        """Контейнер кнопок"""
        buttons_row = QHBoxLayout() # Горизонтальная раскладка для кнопок
        buttons_row.setSpacing(10) # Отступ между элементами по горизонтали
        self.send_button = QPushButton("Отправить команду") # Кнопка отправить команду
        self.send_button.setObjectName("sendCommandButton")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._on_send_clicked)
        self.send_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Разрешить растягивать кнопку по горизонтали и вертикали
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        """Добавление кнопок в контейнер"""
        buttons_row.addWidget(self.send_button)
        buttons_row.addWidget(self.stop_button)
        """Добавление контейнера кнопок в контейнер кнопок и статуса последней команды"""
        actions_container.addLayout(buttons_row)
        """Контейнер статуса последней команды: слева статус, справа время отправки"""
        self.command_status_frame = QFrame()
        self.command_status_frame.setObjectName("nestedPanel")
        status_layout = QHBoxLayout(self.command_status_frame) # Горизонтальная раскладка для статуса последней команды
        status_layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        status_layout.setSpacing(10) # Отступ между элементами по горизонтали
        """Точка статуса"""
        self.command_status_dot = QLabel()
        self.command_status_dot.setFixedSize(10, 10) # Фиксированный размер точки статуса
        self.command_status_dot.setObjectName("statusDotDisconnected")
        self.command_status_dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        """Текст статуса"""
        self.command_status_label = QLabel("Ожидание")
        self.command_status_label.setObjectName("statusLabel")
        """Добавление точки статуса и текста статуса в контейнер статуса"""
        status_layout.addWidget(self.command_status_dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        status_layout.addWidget(self.command_status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        status_layout.addStretch(1)
        self.command_sent_time_label = QLabel()
        self.command_sent_time_label.setVisible(False)
        status_layout.addWidget(
            self.command_sent_time_label,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        actions_container.addWidget(self.command_status_frame)
        main_layout.addStretch(1)
        main_layout.addLayout(actions_container)
        self.set_actuators([]) # Установка списка механизмов
        self._update_motion_fields_enabled() # Обновление состояния полей движения
        self.refresh_command_buttons()

    """Обновление доступности кнопок в зависимости от флага связи"""
    def set_link_connected(self, connected: bool) -> None:
        self._link_connected = connected
        if not connected:
            self._clear_motion_fields()
            self.set_last_command_status("Ожидание", sent_time_text=None)
        self.refresh_command_buttons()

    """Очистить поля положения и скорости (при отключении от контроллера)"""
    def _clear_motion_fields(self) -> None:
        for field in (self.position_edit, self.speed_edit):
            field.clear()
            self._clear_error(field)

    """Проверка возможности отправить основную команду (связь и выбор в комбо)"""
    def _can_send_command(self) -> bool:
        if not self._link_connected:
            return False
        if not self.actuator_combo.isEnabled() or self.actuator_combo.currentData() is None:
            return False
        if not self.action_combo.isEnabled() or self.action_combo.currentData() is None:
            return False
        return True

    """Проверка возможности отправить команду остановки"""
    def _can_stop_command(self) -> bool:
        if not self._link_connected:
            return False
        return self.actuator_combo.isEnabled() and self.actuator_combo.currentData() is not None

    """Обновление состояния кнопок «Отправить» и «Остановить»"""
    def refresh_command_buttons(self) -> None:
        can_send = self._can_send_command()
        can_stop = self._can_stop_command()
        self.send_button.setEnabled(can_send)
        self.stop_button.setEnabled(can_stop)

    def actuator_count(self) -> int:
        if not self.actuator_combo.isEnabled():
            return 0
        return self.actuator_combo.count()

    def _is_move_action(self) -> bool:
        return (
            self.action_combo.isEnabled()
            and str(self.action_combo.currentData()) == "move"
        )

    def _motion_fields_valid(self) -> tuple[bool, bool]:
        if not self._is_move_action():
            return True, True
        return (
            self._validate_motion_field(self.position_edit),
            self._validate_motion_field(self.speed_edit),
        )

    def send_hint_text(self) -> str:
        position_ok, speed_ok = self._motion_fields_valid()
        return explain_send_blocked(
            link_connected=self._link_connected,
            actuator_count=self.actuator_count(),
            has_actuator=self.actuator_combo.currentData() is not None,
            has_action=self.action_combo.currentData() is not None,
            action_is_move=self._is_move_action(),
            position_ok=position_ok,
            speed_ok=speed_ok,
        )

    def stop_hint_text(self) -> str:
        return explain_stop_blocked(
            link_connected=self._link_connected,
            actuator_count=self.actuator_count(),
            has_actuator=self.actuator_combo.currentData() is not None,
        )

    """Обновление состояния полей движения"""
    def _update_motion_fields_enabled(self) -> None:
        is_move = self.action_combo.isEnabled() and str(self.action_combo.currentData()) == "move"
        self.direction_combo.setEnabled(is_move) # Разрешить выбор направления только если выбрано перемещение
        self.position_edit.setEnabled(is_move) # Разрешить ввод положения только если выбрано перемещение
        self.speed_edit.setEnabled(is_move) # Разрешить ввод скорости только если выбрано перемещение
        if not is_move:
            self._clear_error(self.position_edit) # Очистить ошибку в поле ввода положения
            self._clear_error(self.speed_edit) # Очистить ошибку в поле ввода скорости

    """Обработка окончания ввода положения"""
    def _on_position_editing_finished(self) -> None:
        self._validate_motion_field(self.position_edit)
    
    """Обработка окончания ввода скорости"""
    def _on_speed_editing_finished(self) -> None:
        self._validate_motion_field(self.speed_edit)

    def _motion_field_issues(self) -> list[str]:
        if not self._is_move_action():
            return []
        issues: list[str] = []
        position_text = self.position_edit.text().strip()
        if position_text and (not position_text.isdigit() or int(position_text) <= 0):
            issues.append("Положение: целое положительное число или пусто")
        speed_text = self.speed_edit.text().strip()
        if speed_text and (not speed_text.isdigit() or int(speed_text) <= 0):
            issues.append("Скорость: целое положительное число или пусто (по умолчанию)")
        return issues

    """Обработка нажатия кнопки «Отправить команду»"""
    def _on_send_clicked(self) -> None:
        if not self._can_send_command():
            return
        issues = self._motion_field_issues()
        if issues:
            self._validate_motion_fields()
            self.input_validation_failed.emit(issues)
            return
        if not self._validate_motion_fields():
            return
        self.command_send_requested.emit()

    """Обработка нажатия кнопки «Остановить»"""
    def _on_stop_clicked(self) -> None:
        if not self._can_stop_command():
            return
        self.stop_command_requested.emit()

    """Валидация поля движения"""
    def _validate_motion_field(self, field: QLineEdit) -> bool:
        if not field.isEnabled(): # Если поле не активно
            return True
        text = field.text().strip() # Получение текста из поля
        if not text:
            self._clear_error(field)
            return True
        if text.isdigit() and int(text) > 0: # Если текст является числом и больше 0
            self._clear_error(field) # Очистить ошибку в поле
            return True
        hint = (
            "Целое положительное число или пусто"
            if field is self.position_edit
            else "Целое положительное число или пусто (по умолчанию)"
        )
        self._show_error(field, hint)
        return False

    def set_default_speed(self, value: int) -> None:
        self.speed_edit.setPlaceholderText(str(value))

    """Валидация полей движения"""
    def _validate_motion_fields(self) -> bool:
        if not self.position_edit.isEnabled(): # Если поле ввода положения не активно
            return True
        ok = self._validate_motion_field(self.position_edit) # Валидация поля ввода положения
        ok = self._validate_motion_field(self.speed_edit) and ok # Валидация поля ввода скорости и проверка на ошибки
        return ok

    """Текущий выбранный механизм из выпадающего списка"""
    def selected_actuator(self) -> tuple[int, str] | None:
        actuator_id = self.actuator_combo.currentData()
        if actuator_id is None:
            return None
        text = self.actuator_combo.currentText()
        prefix = f"ID: {actuator_id} "
        name = text.removeprefix(prefix).strip() if text.startswith(prefix) else text.strip()
        return int(actuator_id), name or f"ID {actuator_id}"

    """Установить текущий индекс комбо по id механизма"""
    def select_actuator(self, actuator_id: int, *, emit_signal: bool = True) -> bool:
        index = self.actuator_combo.findData(actuator_id)
        if index < 0:
            return False
        block = not emit_signal
        if block:
            self.actuator_combo.blockSignals(True)
        try:
            self.actuator_combo.setCurrentIndex(index)
        finally:
            if block:
                self.actuator_combo.blockSignals(False)
        return True

    """Установка списка механизмов"""
    def set_actuators(
        self,
        actuators: list[tuple[int, str]],
        *,
        select_id: int | None = None,
    ) -> None:
        has_actuators = len(actuators) > 0
        self.actuator_combo.blockSignals(True)
        self.action_combo.blockSignals(True)
        try:
            self.actuator_combo.clear()
            for actuator_id, name in actuators:
                self.actuator_combo.addItem(f"ID: {actuator_id} {name}", actuator_id)
            self.actuator_combo.setEnabled(has_actuators)
            self.action_combo.setEnabled(has_actuators)
            if has_actuators:
                index = 0
                if select_id is not None:
                    found = self.actuator_combo.findData(select_id)
                    if found >= 0:
                        index = found
                self.actuator_combo.setCurrentIndex(index)
        finally:
            self.actuator_combo.blockSignals(False)
            self.action_combo.blockSignals(False)
        self._update_motion_fields_enabled()
        self.refresh_command_buttons()

    """Выпадающий список в стиле приложения (без лишней обводки списка значений)"""
    def _create_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(False)
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        view = QListView()
        view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        view.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setLineWidth(0)
        view.setMidLineWidth(0)
        combo.setView(view)
        return combo

    """Показать ошибку в поле"""
    def _show_error(self, field: QLineEdit, message: str) -> None:
        field.setProperty("error", True) # Установить свойство ошибки в поле
        field.style().unpolish(field) # Убрать стили из поля
        field.style().polish(field) # Применить стили к полю
        hint = self._field_error_labels.get(field)
        if hint is not None:
            hint.setText(message)

    """Очистить ошибку в поле"""
    def _clear_error(self, field: QLineEdit) -> None:
        field.setProperty("error", False) # Установить свойство ошибки в поле
        field.style().unpolish(field) # Убрать стили из поля
        field.style().polish(field) # Применить стили к полю
        hint = self._field_error_labels.get(field)
        if hint is not None:
            hint.setText("")

    """Установка статуса последней команды"""
    def set_last_command_status(
        self,
        status_text: str,
        sent_time_text: str | None = None,
        *,
        dot_object_name: str = "statusDotDisconnected",
    ) -> None:
        self.command_status_label.setText(status_text)
        if sent_time_text:
            self.command_sent_time_label.setText(sent_time_text)
            self.command_sent_time_label.setVisible(True)
        else:
            self.command_sent_time_label.clear()
            self.command_sent_time_label.setVisible(False)
        self._apply_command_status_dot_style(dot_object_name)

    """Применение стиля точки статуса"""
    def _apply_command_status_dot_style(self, object_name: str) -> None:
        self.command_status_dot.setObjectName(object_name)
        self.command_status_dot.style().unpolish(self.command_status_dot)
        self.command_status_dot.style().polish(self.command_status_dot)
