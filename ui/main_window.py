from typing import Any  # тип для значений в словаре конфигурации
from PySide6.QtWidgets import QMainWindow  # базовый виджет «главное окно»

class MainWindow(QMainWindow):  # наследуем стандартное главное окно Qt
    def __init__(self, config: dict[str, Any]) -> None:  # принимаем загруженный JSON как словарь
        super().__init__()  # инициализируем родительский QMainWindow (обязательный вызов)
        self._config = {k: v for k, v in config.items() if not k.startswith("_")}  # убираем служебные ключи вроде _comments
        self.resize(800, 600)  # начальная ширина и высота окна в пикселях
        self.setWindowTitle("Система управления исполнительными механизмами робота")  # текст в заголовке окна