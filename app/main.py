"""ТОЧКА ВХОДА: загрузка конфигурации, запуск главного окна"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import sys # Доступ к sys.argv и к sys.exit для кода выхода процесса
from pathlib import Path
from PySide6.QtWidgets import QApplication, QStyleFactory # Qt-приложение и фабрика стилей
from config.config_loader import load_config # Загрузка словаря конфигурации
from ui.main_window import MainWindow # Главное окно оператора

_STYLES_DIR = Path(__file__).resolve().parent.parent / "ui" / "styles"

"""Запуск приложения: конфигурация, цикл событий Qt"""
def main() -> None: # Точка входа
    config = load_config() # Читаем и проверяем конфигурацию до создания окна
    app = QApplication(sys.argv) # Один объект приложения Qt на весь процесс; sys.argv — параметры ОС
    # Fusion: на macOS нативный стиль игнорирует QSS у QComboBox (рамка, ::drop-down)
    app.setStyle(QStyleFactory.create("Fusion"))
    chevron_icon = (_STYLES_DIR / "icons" / "chevron-down.svg").resolve().as_posix()
    app_qss = (_STYLES_DIR / "app.qss").read_text(encoding="utf-8").replace("%CHEVRON_ICON%", chevron_icon)
    app.setStyleSheet(app_qss)
    window = MainWindow(config) # Создаём главное окно и передаём ему конфигурацию
    window.showMaximized() # Показываем окно развёрнутым на доступную область экрана (не полноэкранный режим)
    sys.exit(app.exec()) # Запускаем цикл обработки событий

if __name__ == "__main__": # Файл запущен напрямую (python -m app.main), а не импортирован как модуль
    main() # Вызываем точку входа
