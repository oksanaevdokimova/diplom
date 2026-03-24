Тема ВКР: Разработка системы управления исполнительными механизмами робота

## Стек
- Python 3.13  
- GUI: PySide6 (Qt 6)  
- Последовательный порт: pyserial (USB-COM)  
- Сеть: `asyncio`, сокеты TCP (Ethernet / Wi‑Fi)  
- Прикладной обмен: JSON  
- Графики / быстрый мониторинг: PyQtGraph  
- Журналы и параметры на ПК: SQLite, текстовые логи; конфигурация — JSON  

Целевые ОС: Windows 10/11, Linux, macOS.

## Установка
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

На Windows (PowerShell):
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Запуск
Из корня репозитория (каталог, где лежат `app/`, `ui/`, `requirements.txt`):
```bash
python -m app.main
```