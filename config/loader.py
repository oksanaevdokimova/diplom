import json  # стандартный модуль для разбора и записи JSON
from pathlib import Path  # класс пути к файлу в файловой системе
from typing import Any  # тип «любое значение» для значений в словаре

def load_json(path: str | Path) -> dict[str, Any]:  # загрузка JSON-объекта в словарь Python
    p = Path(path)  # приводим строку к Path (или оставляем Path без изменений)
    with p.open(encoding="utf-8") as f:  # открываем файл в режиме текста с кодировкой UTF-8
        return json.load(f)  # читаем весь файл и превращаем JSON в объекты Python