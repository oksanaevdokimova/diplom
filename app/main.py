import json  # модуль для исключения JSONDecodeError при разборе конфига
import sys  # модуль для доступа к аргументам командной строки (нужен для QApplication)
from pathlib import Path  # удобные пути к файлам независимо от ОС
from PySide6.QtWidgets import QApplication, QMessageBox  # класс главного объекта любого Qt-приложения с окнами
from config.defaults import CONNECTION_DEFAULTS  # значения подключения, если конфиг не прочитан
from config.loader import load_json  # чтение JSON-файла в словарь
from ui.main_window import MainWindow  # наше главное окно из пакета ui

def _load_connection_config(project_root: Path) -> tuple[dict, str | None]:  # (конфиг, текст предупреждения или None)
    path = project_root / "config" / "local.json"  # абсолютный путь к локальному профилю подключения
    try:  # файл есть и JSON корректен
        return load_json(path), None  # словарь из файла, предупреждение не нужно
    except FileNotFoundError:  # файла нет (не скопировали, неверный путь)
        msg = (  # текст для QMessageBox
            f"Файл не найден:\n{path}\n\n"
            "Будут использованы значения подключения по умолчанию."
        )
        return CONNECTION_DEFAULTS.copy(), msg  # дефолты и сообщение для диалога после создания MainWindow
    except json.JSONDecodeError:  # файл не является корректным JSON (синтаксис, кодировка и т.п.)
        msg = (  # текст для QMessageBox
            f"Не удалось разобрать JSON в файле:\n{path}\n\n"
            "Будут использованы значения подключения по умолчанию."
        )
        return CONNECTION_DEFAULTS.copy(), msg  # дефолты и предупреждение

def main() -> int:  # точка входа: возвращает код выхода процесса (int)
    app = QApplication(sys.argv)  # создаём приложение Qt и передаём ему argv (стандарт для Qt)
    project_root = Path(__file__).resolve().parent.parent  # корень репозитория (на уровень выше каталога app)
    config, warn = _load_connection_config(project_root)  # читаем конфиг; при ошибке — дефолты и текст предупреждения
    window = MainWindow(config=config)  # создаём экземпляр главного окна с переданным словарём настроек
    if warn is not None:  # если загрузка local.json не удалась
        QMessageBox.warning(window, "Конфигурация", warn)  # родитель — окно, а не None (устойчивее на macOS)
    window.show()  # показываем окно на экране
    return app.exec()  # запускаем цикл обработки событий; 0 = нормальный выход

if __name__ == "__main__":  # этот блок выполняется только при прямом запуске файла, не при import
    raise SystemExit(main())  # выходим из процесса с кодом, который вернула main()