"""Сборка command из панели управления"""

from __future__ import annotations
from typing import Any
from protocol.message import AppMessage, make_command
from protocol.types import Action, Direction

def build_stop_command(panel: Any) -> AppMessage:
    """Сборка команды остановки для выбранного механизма"""
    actuator_id = int(panel.actuator_combo.currentData()) # ID выбранного исполнительного механизма
    return make_command(action=Action.STOP, actuator_id=actuator_id) # Сборка команды остановки

def build_command(panel: Any, *, default_speed: int) -> AppMessage | None:
    """Сборка команды move или stop из полей панели управления"""
    actuator_id = int(panel.actuator_combo.currentData()) # ID выбранного исполнительного механизма
    action = str(panel.action_combo.currentData()) # Выбранное действие
    if action == "stop": # Если действие "stop"
        return make_command(action=Action.STOP, actuator_id=actuator_id) # Сборка команды остановки
    if action == "move": # Если действие "move"
        direction = Direction(str(panel.direction_combo.currentData())) # Выбранное направление
        speed_text = panel.speed_edit.text().strip() # Текст из поля ввода скорости
        speed = int(speed_text) if speed_text else default_speed # Преобразование текста в число (если ввели скорость, то берём её; если не ввели, то по умолчанию из конфигурации)
        position_text = panel.position_edit.text().strip() # Текст из поля ввода положения
        position = int(position_text) if position_text else None # Преобразование текста в число (если ввели положение, то берём его; если не ввели, то None)
        return make_command(action=Action.MOVE, actuator_id=actuator_id, direction=direction, speed=speed, position=position) # Сборка команды движения
    return None
