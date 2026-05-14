"""ЗАГРУЗКА И СОХРАНЕНИЕ КОНФИГУРАЦИИ"""

from __future__ import annotations # Чтобы можно было писать аннотации вроде dict[str, Any] без кавычек
import json # Библиотека для разбора и записи JSON в файлы
from copy import deepcopy # Функция для копирования вложенных структур при слиянии конфигов
from pathlib import Path # Класс для работы с путями к файлам и каталогам
from typing import Any # Универсальный тип для значений в словаре конфигурации
from .config_validator import validate_config # Импорт проверки структуры конфигурации

_CONFIG_DIR = Path(__file__).resolve().parent # Каталог, где лежат конфигурационные файлы
_DEFAULT_PATH = _CONFIG_DIR / "default_config.json" # Путь к образцу конфигурации (default_config.json)

"""Путь к встроенному образцу конфигурации (default_config.json)"""
def default_config_path() -> Path: # Функция без аргументов, возвращает Path
    return _DEFAULT_PATH # Путь к образцу конфигурации (default_config.json)

"""Путь к конфигурации оператора (config.json)"""
def user_config_path() -> Path: # Функция без аргументов, возвращает Path
    return _CONFIG_DIR / "config.json" # Путь к конфигурации оператора (config.json) в каталоге config

"""Чтение JSON-объекта из конфигурации в формате словаря"""
def _load_json(path: Path) -> dict[str, Any]: # Читаем JSON-объект из конфигурации (словарь ключ-значение)
    with path.open(encoding="utf-8") as f: # Открываем файл в режиме чтения текста с кодировкой UTF-8
        data = json.load(f) # Парсим весь файл как JSON в объекты Python
    if not isinstance(data, dict): # Проверяем, что в корне JSON лежит объект
        raise ValueError(f"Файл {path} должен содержать JSON-объект в корне") # Ошибка для неверного формата
    return data # Возвращаем словарь с конфигурацией

"""Слияние двух словарей"""
def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]: # Слияние двух словарей с рекурсией по вложенным словарям
    out = deepcopy(base) # Делаем полную копию default_config.json
    for key, value in override.items(): # Проходим по всем парам ключ–значение из config.json
        if key in out and isinstance(out[key], dict) and isinstance(value, dict): # Если ключ уже есть в итоговом словаре, и оба значения — словари
            out[key] = _deep_merge(out[key], value) # Делаем рекурсивное слияние вложенных словарей
        else: # Перезаписываем значение целиком или добавляем новый ключ
            out[key] = deepcopy(value) # Копируем значение из config.json в итоговый словарь
    return out # Возвращаем итоговый словарь

"""Загрузка образца конфигурации (default_config.json)"""
def load_default_config() -> dict[str, Any]: # Загрузка образца конфигурации (словарь ключ-значение)
    return _load_json(_DEFAULT_PATH) # Возвращаем default_config.json

"""Загрузка образца конфигурации (default_config.json) с наложением конфигурации оператора (config.json)"""
def load_config() -> dict[str, Any]: # Загрузка конфигурации (словарь ключ-значение)
    base = load_default_config() # Читаем default_config.json
    path = user_config_path() # Читаем config.json
    if path.is_file(): # Проверяем, существует ли config.json
        user = _load_json(path) # Делаем словарь из config.json
        merged = _deep_merge(base, user) # Делаем слияние значений из config.json с default_config.json
    else: # config.json не существует
        merged = base # Используем словарь default_config.json
    validate_config(merged) # Проверяем конфигурации на корректность
    return merged # Возвращаем проверенный словарь конфигурации

"""Сохранение конфигурации в config.json после проверки"""
def save_config(config: dict[str, Any]) -> None: # Запись конфигурации в config.json после проверки
    validate_config(config) # Проверяем конфигурацию на корректность
    path = user_config_path() # Читаем config.json
    path.parent.mkdir(parents=True, exist_ok=True) # Создаём родительский каталог, если его ещё нет
    with path.open("w", encoding="utf-8") as f: # Открываем файл для записи текста в UTF-8
        json.dump(config, f, ensure_ascii=False, indent=2) # Записываем конфигурацию в файл в формате JSON
        f.write("\n") # Добавляем перевод строки в конце файла