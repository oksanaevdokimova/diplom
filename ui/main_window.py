from PySide6.QtWidgets import QMainWindow  # базовый виджет «главное окно»

class MainWindow(QMainWindow):  # наследуем стандартное главное окно Qt
    def __init__(self) -> None:  # конструктор вызывается при MainWindow()
        super().__init__()  # инициализируем родительский QMainWindow (обязательный вызов)
        self.setWindowTitle("Система управления исполнительными механизмами робота")  # текст в заголовке окна
        self.resize(800, 600)  # начальная ширина и высота окна в пикселях