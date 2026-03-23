import sys  # модуль для доступа к аргументам командной строки (нужен для QApplication)
from PySide6.QtWidgets import QApplication  # класс главного объекта любого Qt-приложения с окнами
from ui.main_window import MainWindow  # наше главное окно из пакета ui

def main() -> int:  # точка входа: возвращает код выхода процесса (int)
    app = QApplication(sys.argv)  # создаём приложение Qt и передаём ему argv (стандарт для Qt)
    window = MainWindow()  # создаём экземпляр главного окна (пока ещё невидим)
    window.show()  # показываем окно на экране
    return app.exec()  # запускаем цикл обработки событий; 0 = нормальный выход

if __name__ == "__main__":  # этот блок выполняется только при прямом запуске файла, не при import
    raise SystemExit(main())  # выходим из процесса с кодом, который вернула main()