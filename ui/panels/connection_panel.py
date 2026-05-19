"""Панель подключения к контроллеру"""

from __future__ import annotations
from copy import deepcopy
from typing import Any
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
from config.config_loader import save_config
from config.config_validator import validate_config

"""Надписи + поля ввода/выбора с ошибкой при валидации"""
class FieldGroup(QWidget):
    def __init__( self, label_text: str, control: QWidget, width: int, panel: ConnectionPanel) -> None:
        super().__init__()
        """Контейнер для группы надписи + поля ввода/выбора с ошибкой при валидации"""
        field_group_grid = QGridLayout(self)
        field_group_grid.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        field_group_grid.setHorizontalSpacing(10) # Отступ между надписью и полем ввода/выбора
        field_group_grid.setVerticalSpacing(2) # Отступ между ошибкой и строкой «надпись + поле»
        """Надпись"""
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        """Поле ввода/выбора"""
        control.setFixedWidth(width) # Ширина поля ввода/выбора
        control.setFixedHeight(35) # Высота поля ввода/выбора
        control.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Фиксированная ширина и высота поля ввода/выбора
        """Ошибка при валидации"""
        self.error_label = QLabel("")
        self.error_label.setObjectName("fieldError")
        self.error_label.setWordWrap(True) # Перенос текста ошибки при валидации на новую строку
        self.error_label.setVisible(False) # Скрытие ошибки при валидации
        self.error_label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred) # Фиксированная ширина ошибки при валидации
        error_width = (label.sizeHint().width() + field_group_grid.horizontalSpacing() + width) # Ширина ошибки при валидации = ширина надписи + отступ + ширина поля ввода/выбора
        self.error_label.setMaximumWidth(error_width) # Максимальная ширина ошибки при валидации = ширина ошибки при валидации
        field_group_grid.setColumnStretch(0, 0) # Не растягивать первый столбец
        field_group_grid.setColumnStretch(1, 0) # Не растягивать второй столбец
        field_group_grid.addWidget(label, 0, 0) # Надпись в первой ячейке
        field_group_grid.addWidget(control, 0, 1) # Поле ввода/выбора во второй ячейке
        field_group_grid.addWidget(self.error_label, 1, 0, 1, 2) # Ошибка при валидации в третьей ячейке
        """Подключение сигналов"""
        if isinstance(control, QLineEdit):
            control.textChanged.connect(lambda: panel._clear_error(control))
            panel._field_error_labels[control] = self.error_label

"""Панель подключения"""
class ConnectionPanel(QFrame):
    config_saved = Signal(dict)
    connection_changed = Signal(bool)
    connect_requested = Signal(dict)
    connect_fields_invalid = Signal(list)
    disconnect_requested = Signal()
    PANEL_HEIGHT = 120
    _DYNAMIC_FIELD_ATTRS = ( # Список атрибутов динамических полей
        "usb_port_edit",
        "usb_baudrate_edit",
        "wifi_host_edit",
        "wifi_port_edit",
        "gsm_mode_combo",
        "gsm_host_edit",
        "gsm_port_edit",
        "gsm_broker_host_edit",
        "gsm_broker_port_edit",
        "gsm_topic_command_edit",
        "gsm_topic_messages_edit",
    )

    """Конструктор панели подключения"""
    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = deepcopy(config) # Копия конфигурации
        self._field_error_labels: dict[QLineEdit, QLabel] = {}
        self._building_dynamic_fields = False # Флаг для предотвращения рекурсивного вызова _build_dynamic_fields
        self._gsm_mode = str(self._config.get("gsm", {}).get("mode", "mqtt")) # Режим GSM по умолчанию
        self._build_ui() # Построение интерфейса
        self._load_values_from_config() # Загрузка значений из конфигурации
        self._build_dynamic_fields() # Построение динамических полей для выбранного канала

    """Структура панели подключения"""
    def _build_ui(self) -> None:
        """Общие настройки для панели"""
        self.setObjectName("panel")
        self.setFixedHeight(self.PANEL_HEIGHT) # Фиксированная высота панели
        main_layout = QVBoxLayout(self) # Вертикальная раскладка для панели
        main_layout.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        main_layout.setSpacing(0) # Чтобы не было лишних отступов

        """Контейнер заголовка: слева название, справа кнопки и статус"""
        header_container = QHBoxLayout()
        header_container.setSpacing(10) # Отступ между кнопками и статусом
        """Название панели"""
        self.title_label = QLabel("Панель подключения")
        self.title_label.setObjectName("panelTitle")
        header_container.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) # Выравнивание по левому краю и по верху
        header_container.addStretch(1) # Пустое место от названия панели до кнопок и статуса
        """Контейнер кнопок и статуса"""
        header_actions_container = QHBoxLayout()
        header_actions_container.setSpacing(10) # Отступ между кнопками и статусом
        """Кнопка подключения"""
        self.connect_button = QPushButton("Подключить")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        """Кнопка отключения"""
        self.disconnect_button = QPushButton("Отключить")
        self.disconnect_button.setObjectName("disconnectButton")
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        """Контейнер статуса"""
        self.status_frame = QFrame()
        self.status_frame.setObjectName("connectionStatus")
        status_container = QHBoxLayout(self.status_frame)
        status_container.setContentsMargins(0, 0, 0, 0) # Чтобы не было лишних отступов
        status_container.setSpacing(10) # Отступ между точкой и текстом статуса
        status_container.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter) # Выравнивание по центру по горизонтали и вертикали
        """Точка статуса"""
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10) # Фиксированный размер точки статуса
        self.status_dot.setObjectName("statusDotDisconnected")
        self.status_dot.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        """Текст статуса"""
        self.status_label = QLabel("Отключено")
        self.status_label.setObjectName("statusLabel")
        """Добавление элементов в контейнер статуса"""
        status_container.addStretch(1)
        status_container.addWidget(self.status_dot)
        status_container.addWidget(self.status_label)
        status_container.addStretch(1)
        """Добавление элементов в контейнер кнопок и статуса"""
        header_actions_container.addWidget(self.connect_button)
        header_actions_container.addWidget(self.disconnect_button)
        header_actions_container.addWidget(self.status_frame)
        """Добавление контейнера кнопок и статуса в контейнер заголовка"""
        header_container.addLayout(header_actions_container)
        """Добавление контейнера заголовка в тело панели"""
        main_layout.addLayout(header_container)
        self.show_disconnected()

        """Тело панели"""
        main_layout.addStretch(1) # Пустое место от заголовка (чтоб центрировать в оставшемся пространстве)
        """Контейнер для надписей + полей ввода/выбора"""
        fields_container = QHBoxLayout() # Контейнер: надписи + поля ввода/выбора
        fields_container.setSpacing(10) # Отступ от канала связи до контейнера для динамических надписей + полей ввода/выбора
        fields_container.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter) # Выравнивание по левому краю и по центру по вертикали
        """Список каналов связи"""
        self.transport_combo = self._create_combo() # Создание выпадающего списка для выбора канала связи
        self.transport_combo.addItem("USB-COM", "usb")
        self.transport_combo.addItem("Wi-Fi", "wifi")
        self.transport_combo.addItem("GSM", "gsm")
        self.transport_combo.currentIndexChanged.connect(self._build_dynamic_fields) # При выборе изменяются динамические поля
        """Канал связи + список каналов связи"""
        transport_group = FieldGroup("Канал связи:", self.transport_combo, 110, self)
        fields_container.addWidget(transport_group)
        """Контейнер для динамических надписей + полей ввода/выбора"""
        self.dynamic_fields_container = QHBoxLayout() # Контейнер: динамическиенадписи + поля ввода/выбора
        self.dynamic_fields_container.setSpacing(10)
        """Вложенность контейнеров"""
        fields_container.addLayout(self.dynamic_fields_container)
        main_layout.addLayout(fields_container)
        main_layout.addStretch(1) # Пустое место от контейнера до края панели (чтоб центрировать в оставшемся пространстве)

    """Создание выпадающего списка для выбора значения"""
    def _create_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(False) # Нельзя редактировать текст в выпадающем списке
        combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Можно получить обводку при нажатии на выпадающий список
        view = QListView() # Создание списка значений для выпадающего списка
        view.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Не получать обводку при нажатии на список значений
        view.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False) # Не показывать обводку при нажатии на список значений
        view.setFrameShape(QFrame.Shape.NoFrame) # Не рисовать рамку для списка значений
        view.setLineWidth(0) # Ширина рамки
        view.setMidLineWidth(0) # Ширина средней линии рамки
        combo.setView(view) # Добавление списка значений в выпадающий список
        return combo # Возвращение выпадающего списка

    """Загрузка значений из конфигурации"""
    def _load_values_from_config(self) -> None:
        active_transport = self._config.get("active_transport", "usb") # Выбранный канал связи из конфигурации
        self.transport_combo.blockSignals(True) # Блокировка сигналов выпадающего списка
        try: # Попытка установить выбранный канал связи из конфигурации
            for index in range(self.transport_combo.count()): # Перебор всех значений в выпадающем списке
                if self.transport_combo.itemData(index) == active_transport: # Если значение совпадает с выбранным каналом связи
                    self.transport_combo.setCurrentIndex(index) # Установка выбранного значения
                    break
        finally:
            self.transport_combo.blockSignals(False)

    """Удаление атрибутов динамических полей"""
    def _drop_dynamic_field_attrs(self) -> None:
        for name in self._DYNAMIC_FIELD_ATTRS: # Перебор всех атрибутов динамических полей
            try: # Попытка удаления атрибута
                delattr(self, name) # Удаление атрибута
            except AttributeError:
                pass # Если атрибут не существует, пропускаем ошибку

    """Очистка динамических полей"""
    def _clear_dynamic_fields(self) -> None:
        try: # Попытка отключить сигнал изменения выбранного режима GSM
            self.gsm_mode_combo.currentIndexChanged.disconnect(self._on_gsm_mode_changed)
        except (AttributeError, RuntimeError):
            pass # Если сигнал не был подключен, пропускаем ошибку
        while self.dynamic_fields_container.count(): # Очистка контейнера для динамических полей
            item = self.dynamic_fields_container.takeAt(0) # Удаление первого элемента из контейнера
            widget = item.widget() # Получение виджета из элемента
            if widget is not None: # Если виджет не None, блокируем сигналы и удаляем его
                widget.blockSignals(True) # Блокировка сигналов виджета
                widget.deleteLater() # Удаление виджета
        self._field_error_labels.clear() # Очистка словаря ошибок под полями
        self._drop_dynamic_field_attrs() # Удаление атрибутов динамических полей

    """Обработка изменения выбранного режима GSM"""
    def _on_gsm_mode_changed(self, _index: int = 0) -> None:
        self._gsm_mode = str(self.gsm_mode_combo.currentData()) # Установка выбранного режима GSM
        self._build_dynamic_fields() # Построение динамических полей в зависимости от выбранного канала связи

    """Добавление поля ввода с подписью"""
    def _add_labeled_field(self, label_text: str, field_name: str, value: str, width: int = 100) -> QLineEdit:
        field = QLineEdit()
        field.setObjectName(field_name) # Установка имени поля ввода
        field.setText(value) # Установка значения поля ввода
        group = FieldGroup(label_text, field, width, self) # Создание группы надписи + поля ввода с ошибкой при валидации
        self.dynamic_fields_container.addWidget(group) # Добавление группы в контейнер для динамических полей
        return field # Возвращение поля ввода

    """Добавление выпадающего списка с подписью"""
    def _add_labeled_combo(self, label_text: str, field_name: str, values: list[tuple[str, str]], current_value: str, width: int = 100) -> QComboBox:
        combo = self._create_combo()
        combo.setObjectName(field_name)
        for text, data in values: # Добавление значений в выпадающий список
            combo.addItem(text, data)
        for index in range(combo.count()): # Перебор всех значений в выпадающем списке
            if combo.itemData(index) == current_value: # Если значение совпадает с выбранным значением
                combo.setCurrentIndex(index) # Установка выбранного значения
                break
        group = FieldGroup(label_text, combo, width, self) # Создание группы надписи + выпадающего списка с ошибкой при валидации
        self.dynamic_fields_container.addWidget(group) # Добавление группы в контейнер для динамических полей
        return combo # Возвращение выпадающего списка

    """Построение динамических полей в зависимости от выбранного канала связи"""
    def _build_dynamic_fields(self) -> None:
        if self._building_dynamic_fields: # Если флаг установлен, пропускаем построение динамических полей
            return
        self._building_dynamic_fields = True # Установка флага
        try:
            self._build_dynamic_fields_impl() # Построение динамических полей в зависимости от выбранного канала связи
        finally:
            self._building_dynamic_fields = False # Сброс флага

    """Реализация построения динамических полей в зависимости от выбранного канала связи"""
    def _build_dynamic_fields_impl(self) -> None:
        transport = self._current_transport()
        self._clear_dynamic_fields() # Очистка динамических полей
        self._clear_field_errors() # Очистка ошибок под полями
        """Построение динамических полей в зависимости от выбранного канала связи"""
        if transport == "usb":
            usb = self._config.get("usb", {})
            self.usb_port_edit = self._add_labeled_field(
                "Порт:",
                "usb_port",
                str(usb.get("port", "")),
                110,
            )
            self.usb_baudrate_edit = self._add_labeled_field(
                "Скорость:",
                "usb_baudrate",
                str(usb.get("baudrate", "")),
                110,
            )
        elif transport == "wifi":
            wifi = self._config.get("wifi", {})
            self.wifi_host_edit = self._add_labeled_field(
                "Хост:",
                "wifi_host",
                str(wifi.get("host", "")),
                130,
            )
            self.wifi_port_edit = self._add_labeled_field(
                "Порт:",
                "wifi_port",
                str(wifi.get("port", "")),
                110,
            )
        elif transport == "gsm":
            gsm = self._config.get("gsm", {})
            mode = self._gsm_mode or str(gsm.get("mode", "mqtt"))
            self._gsm_mode = mode

            self.gsm_mode_combo = self._add_labeled_combo(
                "Режим:",
                "gsm_mode",
                [("MQTT", "mqtt"), ("TCP", "tcp")],
                mode,
                100,
            )
            self.gsm_mode_combo.currentIndexChanged.connect(self._on_gsm_mode_changed)
            if mode == "tcp":
                self.gsm_host_edit = self._add_labeled_field(
                    "Хост:",
                    "gsm_host",
                    str(gsm.get("host", "")),
                    130,
                )

                self.gsm_port_edit = self._add_labeled_field(
                    "Порт:",
                    "gsm_port",
                    str(gsm.get("port", "")),
                    110,
                )
            else:
                self.gsm_broker_host_edit = self._add_labeled_field(
                    "Брокер:",
                    "gsm_broker_host",
                    str(gsm.get("broker_host", "")),
                    190,
                )
                self.gsm_broker_port_edit = self._add_labeled_field(
                    "Порт:",
                    "gsm_broker_port",
                    str(gsm.get("broker_port", "")),
                    110,
                )
                self.gsm_topic_command_edit = self._add_labeled_field(
                    "Топик команд:",
                    "gsm_topic_command",
                    str(gsm.get("topic_command", "")),
                    160,
                )
                self.gsm_topic_messages_edit = self._add_labeled_field(
                    "Топик сообщений:",
                    "gsm_topic_messages",
                    str(gsm.get("topic_messages", "")),
                    160,
                )

    """Получение выбранного канала связи"""
    def _current_transport(self) -> str:
        return str(self.transport_combo.currentData())

    """Получение выбранного режима GSM"""
    def _current_gsm_mode(self) -> str:
        if self._current_transport() == "gsm": # Если выбран канал связи GSM
            return str(self.gsm_mode_combo.currentData())
        return self._gsm_mode # Возвращение выбранного режима GSM

    """Создание новой конфигурации из полей панели"""
    def _collect_config_from_fields(self) -> dict[str, Any]:
        new_config = deepcopy(self._config) # Копирование конфигурации
        transport = self._current_transport()
        new_config["active_transport"] = transport
        if transport == "usb":
            new_config["usb"] = { # Установка значений для канала связи USB
                "port": self.usb_port_edit.text().strip(), # Установка порта
                "baudrate": int(self.usb_baudrate_edit.text().strip()), # Установка скорости
            }
        elif transport == "wifi":
            new_config["wifi"] = { # Установка значений для канала связи WiFi
                "host": self.wifi_host_edit.text().strip(), # Установка хоста
                "port": int(self.wifi_port_edit.text().strip()), # Установка порта
            }
        elif transport == "gsm":
            mode = self._current_gsm_mode()
            if mode == "tcp":
                new_config["gsm"] = { # Установка значений для канала связи GSM
                    "mode": "tcp",
                    "host": self.gsm_host_edit.text().strip(), # Установка хоста
                    "port": int(self.gsm_port_edit.text().strip()), # Установка порта
                }
            else:
                new_config["gsm"] = { # Установка значений для канала связи GSM
                    "mode": "mqtt",
                    "broker_host": self.gsm_broker_host_edit.text().strip(), # Установка хоста MQTT-брокера
                    "broker_port": int(self.gsm_broker_port_edit.text().strip()), # Установка порта MQTT-брокера
                    "topic_command": self.gsm_topic_command_edit.text().strip(), # Установка топика команд
                    "topic_messages": self.gsm_topic_messages_edit.text().strip(), # Установка топика сообщений
                }
        return new_config

    """Проверка, что строковое поле не пустое"""
    def _require_nonempty_field(self, field: QLineEdit, message: str) -> bool:
        if not field.text().strip(): # Если поле пустое
            self._show_error(field, message)
            return False
        return True

    """Проверка, что поле содержит положительное целое число"""
    def _require_positive_int_field(self, field: QLineEdit, message: str) -> bool:
        text = field.text().strip()
        if not text.isdigit(): # Если поле не содержит положительное целое число
            self._show_error(field, message)
            return False
        if int(text) <= 0: # Если поле содержит отрицательное или нулевое число
            self._show_error(field, message)
            return False
        return True

    """Проверка всех видимых полей панели и показа ошибок"""
    def _validate_visible_fields(self) -> bool:
        ok = True # Флаг для проверки всех видимых полей панели
        transport = self._current_transport()
        if transport == "usb":
            ok &= self._require_nonempty_field(
                self.usb_port_edit,
                "Порт не должен быть пустым",
            )
            ok &= self._require_positive_int_field(
                self.usb_baudrate_edit,
                "Скорость должна быть целым положительным числом",
            )
        elif transport == "wifi":
            ok &= self._require_nonempty_field(
                self.wifi_host_edit,
                "Хост не должен быть пустым",
            )
            ok &= self._require_positive_int_field(
                self.wifi_port_edit,
                "Порт должен быть целым положительным числом",
            )
        elif transport == "gsm":
            mode = self._current_gsm_mode()
            if mode == "tcp":
                ok &= self._require_nonempty_field(
                    self.gsm_host_edit,
                    "Хост не должен быть пустым",
                )
                ok &= self._require_positive_int_field(
                    self.gsm_port_edit,
                    "Порт должен быть целым положительным числом",
                )
            else:
                ok &= self._require_nonempty_field(
                    self.gsm_broker_host_edit,
                    "Брокер не должен быть пустым",
                )
                ok &= self._require_positive_int_field(
                    self.gsm_broker_port_edit,
                    "Порт должен быть целым положительным числом",
                )
                ok &= self._require_nonempty_field(
                    self.gsm_topic_command_edit,
                    "Топик команд не должен быть пустым",
                )
                ok &= self._require_nonempty_field(
                    self.gsm_topic_messages_edit,
                    "Топик сообщений не должен быть пустым",
                )
        return ok

    def _visible_field_issues(self) -> list[str]:
        """Список ошибок видимых полей без изменения подсветки."""
        issues: list[str] = []
        transport = self._current_transport()
        if transport == "usb":
            if not self.usb_port_edit.text().strip():
                issues.append("COM-порт: порт не должен быть пустым")
            text = self.usb_baudrate_edit.text().strip()
            if not text.isdigit() or int(text) <= 0:
                issues.append("Скорость: целое положительное число")
        elif transport == "wifi":
            if not self.wifi_host_edit.text().strip():
                issues.append("Хост: не должен быть пустым")
            text = self.wifi_port_edit.text().strip()
            if not text.isdigit() or int(text) <= 0:
                issues.append("Порт: целое положительное число")
        elif transport == "gsm":
            mode = self._current_gsm_mode()
            if mode == "tcp":
                if not self.gsm_host_edit.text().strip():
                    issues.append("Хост: не должен быть пустым")
                text = self.gsm_port_edit.text().strip()
                if not text.isdigit() or int(text) <= 0:
                    issues.append("Порт: целое положительное число")
            else:
                if not self.gsm_broker_host_edit.text().strip():
                    issues.append("Брокер: не должен быть пустым")
                text = self.gsm_broker_port_edit.text().strip()
                if not text.isdigit() or int(text) <= 0:
                    issues.append("Порт брокера: целое положительное число")
                if not self.gsm_topic_command_edit.text().strip():
                    issues.append("Топик команд: не должен быть пустым")
                if not self.gsm_topic_messages_edit.text().strip():
                    issues.append("Топик сообщений: не должен быть пустым")
        return issues

    """Обработка нажатия кнопки «Подключить»"""
    def _on_connect_clicked(self) -> None:
        self._clear_field_errors()
        issues = self._visible_field_issues()
        if issues:
            self._validate_visible_fields()
            self.connect_fields_invalid.emit(issues)
            self.show_disconnected()
            return
        if not self._validate_visible_fields():
            self.show_disconnected()
            return
        try:
            new_config = self._collect_config_from_fields()
            validate_config(new_config)
        except ValueError as exc:
            self.connect_fields_invalid.emit([str(exc)])
            self.show_disconnected()
            return
        self._config = new_config
        save_config(self._config)
        self.config_saved.emit(deepcopy(self._config))
        self.show_connecting()
        self.connect_requested.emit(deepcopy(self._config))

    """Обработка нажатия кнопки «Отключить»"""
    def _on_disconnect_clicked(self) -> None:
        self.disconnect_requested.emit()

    def show_connecting(self) -> None:
        self.status_label.setText("Подключение...")
        self._apply_status_dot_style("statusDotDisconnected")
        self._apply_status_frame_style(connected=False)
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(False)

    """Показывает ошибку над полем"""
    def _show_error(self, field: QLineEdit, message: str) -> None:
        field.setProperty("error", True)
        field.style().unpolish(field) # Удаление стиля из поля
        field.style().polish(field) # Применение стиля к полю
        hint = self._field_error_labels.get(field) # Получение ошибки под полем
        if hint is not None:
            hint.setFixedHeight(20) # Установка высоты ошибки
            hint.setVisible(True) # Показывает ошибку под полем
            hint.setText(message) # Установка текста ошибки

    """Очистка ошибки над полем"""
    def _clear_error(self, field: QLineEdit) -> None:
        field.setProperty("error", False)
        field.style().unpolish(field) # Удаление стиля из поля
        field.style().polish(field) # Применение стиля к полю
        hint = self._field_error_labels.get(field) # Получение ошибки под полем
        if hint is not None:
            hint.setText("") # Установка текста ошибки
            hint.setFixedHeight(0) # Установка высоты ошибки
            hint.setVisible(False) # Скрывает ошибку под полем

    """Очистка ошибок со всех полей панели"""
    def _clear_field_errors(self) -> None:
        for field in list(self._field_error_labels):
            self._clear_error(field) # Очистка ошибки под полем

    """Установка статуса «Подключено»"""
    def show_connected(self) -> None:
        self.status_label.setText("Подключено") # Установка текста статуса «Подключено»
        self._apply_status_dot_style("statusDotConnected") # Применение стиля для точки статуса
        self._apply_status_frame_style(connected=True) # Применение стиля для рамки статуса
        self.connect_button.setEnabled(False) # Отключение кнопки «Подключить»
        self.disconnect_button.setEnabled(True) # Включение кнопки «Отключить»  
        self.connection_changed.emit(True) # Сигнал о том, что соединение установлено

    """Установка статуса «Отключено»"""
    def show_disconnected(self) -> None:
        self.status_label.setText("Отключено") # Установка текста статуса «Отключено»
        self._apply_status_dot_style("statusDotDisconnected") # Применение стиля для точки статуса
        self._apply_status_frame_style(connected=False) # Применение стиля для рамки статуса
        self.connect_button.setEnabled(True) # Включение кнопки «Подключить»
        self.disconnect_button.setEnabled(False) # Отключение кнопки «Отключить»
        self.connection_changed.emit(False) # Сигнал о том, что соединение разорвано

    """Применение стиля для точки статуса"""
    def _apply_status_dot_style(self, object_name: str) -> None:
        self.status_dot.setObjectName(object_name) # Установка имени объекта для точки статуса
        self.status_dot.style().unpolish(self.status_dot) # Удаление стиля из точки статуса
        self.status_dot.style().polish(self.status_dot) # Применение стиля к точке статуса

    """Применение стиля для рамки статуса"""
    def _apply_status_frame_style(self, *, connected: bool) -> None:
        self.status_frame.setProperty("connected", connected) # Установка свойства соединения для рамки статуса
        self.status_frame.style().unpolish(self.status_frame) # Удаление стиля из рамки статуса
        self.status_frame.style().polish(self.status_frame) # Применение стиля к рамке статуса