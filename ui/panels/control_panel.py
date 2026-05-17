"""Панель управления выбранным механизмом."""

from __future__ import annotations
from PySide6.QtCore import Qt
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

"""Надпись + поле ввода/выбора"""
class ControlFieldGroup(QWidget):
    """Конструктор надписи + поля ввода/выбора"""
    def __init__(self, label_text: str, control: QWidget, width: int, panel: ControlPanel, *, suffix: str | None = None, expand: bool = False) -> None:
        super().__init__()
        """Контейнер для группы надписи + поля ввода/выбора"""
        field_group_grid = QGridLayout(self)
        field_group_grid.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        field_group_grid.setHorizontalSpacing(10) # Отступ между надписью и полем ввода/выбора
        field_group_grid.setVerticalSpacing(2) # Отступ между ошибкой и строкой «надпись + поле»
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
        """Ошибка при валидации"""
        self.error_label = QLabel("")
        self.error_label.setObjectName("fieldError")
        self.error_label.setWordWrap(True) # Перенос текста ошибки при валидации на новую строку
        self.error_label.setVisible(False) # Скрытие ошибки при валидации
        self.error_label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred) # Фиксированная ширина ошибки при валидации
        if not expand:
            error_width = label.sizeHint().width() + field_group_grid.horizontalSpacing() + width # Ширина ошибки при валидации = ширина надписи + отступ + ширина поля ввода/выбора
            self.error_label.setMaximumWidth(error_width) # Максимальная ширина ошибки при валидации = ширина ошибки при валидации
        field_group_grid.addWidget(label, 0, 0) # Надпись в первой ячейке
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
                control_row.addWidget(control, 1) # Поле ввода/выбора во второй ячейке
            else:
                control_row.addWidget(control) # Поле ввода/выбора во второй ячейке
            control_row.addWidget(suffix_label) # Надпись с суффиксом в третьей ячейке
            if not expand:
                control_row.addStretch(1) # Разрешить растягивать поле ввода/выбора с суффиксом по вертикали
            field_group_grid.addWidget(control_cell, 0, 1) # Поле ввода/выбора с суффиксом во второй ячейке
        else:
            field_group_grid.addWidget(control, 0, 1) # Поле ввода/выбора во второй ячейке

        field_group_grid.addWidget(self.error_label, 1, 0, 1, 2) # Ошибка при валидации в третьей ячейке
        if isinstance(control, QLineEdit): # Если поле ввода/выбора является полем ввода
            control.textChanged.connect(lambda: panel._clear_error(control))
            panel._field_error_labels[control] = self.error_label # Ошибка при валидации для поля ввода/выбора

"""Панель управления выбранным механизмом"""
class ControlPanel(QFrame):

    """Конструктор панели управления выбранным механизмом"""
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._field_error_labels: dict[QLineEdit, QLabel] = {}
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
        fields_container.addWidget(ControlFieldGroup("Механизм:", self.actuator_combo, 0, self, expand=True))
        """Список действий"""
        self.action_combo = self._create_combo() # Создание выпадающего списка для выбора действия
        self.action_combo.addItem("Перемещение", "move")
        self.action_combo.addItem("Остановка", "stop")
        self.action_combo.setEnabled(False)
        self.action_combo.currentIndexChanged.connect(self._update_motion_fields_enabled) # Соединение сигнала currentIndexChanged с методом _update_motion_fields_enabled
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
        params_row.addWidget(ControlFieldGroup("Положение:", self.position_edit, 0, self, suffix="ед.", expand=True),1)
        self.speed_edit = QLineEdit() # Поле ввода для скорости
        self.speed_edit.setEnabled(False)
        self.speed_edit.editingFinished.connect(self._on_speed_editing_finished)
        params_row.addWidget(ControlFieldGroup("Скорость:", self.speed_edit, 0, self, suffix="ед./с", expand=True),1)
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
        """Время отправки"""
        self.command_sent_time_label = QLabel("—")
        status_layout.addWidget(self.command_sent_time_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        """Добавление контейнера статуса в контейнер кнопок и статуса последней команды"""
        actions_container.addWidget(self.command_status_frame)
        main_layout.addStretch(1)
        main_layout.addLayout(actions_container)
        self.set_actuators([]) # Установка списка механизмов
        self._update_motion_fields_enabled() # Обновление состояния полей движения

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

    """Обработка нажатия кнопки «Отправить команду»"""
    def _on_send_clicked(self) -> None:
        if not self._validate_motion_fields():
            return

    """Валидация поля движения"""
    def _validate_motion_field(self, field: QLineEdit) -> bool:
        if not field.isEnabled(): # Если поле не активно
            return True
        text = field.text().strip() # Получение текста из поля
        if not text: # Если текст пустой
            self._clear_error(field) # Очистить ошибку в поле
            return True
        if text.isdigit() and int(text) > 0: # Если текст является числом и больше 0
            self._clear_error(field) # Очистить ошибку в поле
            return True
        self._show_error(field, "Должно быть целым положительным числом") # Показать ошибку в поле
        return False

    """Валидация полей движения"""
    def _validate_motion_fields(self) -> bool:
        if not self.position_edit.isEnabled(): # Если поле ввода положения не активно
            return True
        ok = self._validate_motion_field(self.position_edit) # Валидация поля ввода положения
        ok = self._validate_motion_field(self.speed_edit) and ok # Валидация поля ввода скорости и проверка на ошибки
        return ok

    """Установка списка механизмов"""
    def set_actuators(self, actuators: list[tuple[int, str]]) -> None:
        has_actuators = len(actuators) > 0 # Если список механизмов не пустой
        self.actuator_combo.blockSignals(True) # Заблокировать сигналы выпадающего списка для выбора механизма
        self.action_combo.blockSignals(True) # Заблокировать сигналы выпадающего списка для выбора механизма и действия
        try:
            self.actuator_combo.clear() # Очистить выпадающий список для выбора механизма
            for actuator_id, name in actuators:
                self.actuator_combo.addItem(f"ID: {actuator_id} {name}", actuator_id) # Добавить механизм в выпадающий список
            self.actuator_combo.setEnabled(has_actuators)
            self.action_combo.setEnabled(has_actuators) # Разрешить выбор действия только если выбран механизм
        finally:
            self.actuator_combo.blockSignals(False) # Разблокировать сигналы выпадающего списка для выбора механизма
            self.action_combo.blockSignals(False) # Разблокировать сигналы выпадающего списка для выбора механизма и действия
        self._update_motion_fields_enabled() # Обновление состояния полей движения

    """Создание выпадающего списка"""
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
        if hint is not None: # Если ошибка не пустая
            hint.setFixedHeight(20) # Установить высоту ошибки
            hint.setVisible(True) # Показать ошибку
            hint.setText(message) # Установить текст ошибки

    """Очистить ошибку в поле"""
    def _clear_error(self, field: QLineEdit) -> None:
        field.setProperty("error", False) # Установить свойство ошибки в поле
        field.style().unpolish(field) # Убрать стили из поля
        field.style().polish(field) # Применить стили к полю
        hint = self._field_error_labels.get(field)
        if hint is not None: # Если ошибка не пустая
            hint.setText("")
            hint.setFixedHeight(0) # Установить высоту ошибки
            hint.setVisible(False) # Скрыть ошибку

    """Установка статуса последней команды"""
    def set_last_command_status(self, status_text: str, sent_time_text: str, *, dot_object_name: str = "statusDotDisconnected") -> None:
        self.command_status_label.setText(status_text)
        self.command_sent_time_label.setText(sent_time_text)
        self._apply_command_status_dot_style(dot_object_name)

    """Применение стиля точки статуса"""
    def _apply_command_status_dot_style(self, object_name: str) -> None:
        self.command_status_dot.setObjectName(object_name)
        self.command_status_dot.style().unpolish(self.command_status_dot)
        self.command_status_dot.style().polish(self.command_status_dot)
