"""Сохранение журнала и диагностики между запусками приложения."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SESSION_DIR = Path(__file__).resolve().parent.parent / "data"
_LOG_PATH = _SESSION_DIR / "event_log_session.json"
_DIAGNOSTIC_PATH = _SESSION_DIR / "diagnostic_session.json"


def _ensure_session_dir() -> None:
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)


def save_log_entries(entries: list[tuple[str, str, str]]) -> None:
    _ensure_session_dir()
    payload = [{"time": t, "event": e, "description": d} for t, e, d in entries]
    _LOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_log_entries() -> list[tuple[str, str, str]]:
    if not _LOG_PATH.is_file():
        return []
    try:
        data = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    rows: list[tuple[str, str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rows.append(
            (
                str(item.get("time", "")),
                str(item.get("event", "")),
                str(item.get("description", "")),
            ),
        )
    return rows


def save_diagnostic_rows(rows: list[tuple[str, str, str, str, str]]) -> None:
    _ensure_session_dir()
    payload = [
        {
            "time": time_text,
            "level": level,
            "code": code,
            "message": message,
            "source": source,
        }
        for time_text, level, code, message, source in rows
    ]
    _DIAGNOSTIC_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_diagnostic_rows() -> list[tuple[str, str, str, str, str]]:
    if not _DIAGNOSTIC_PATH.is_file():
        return []
    try:
        data = json.loads(_DIAGNOSTIC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    rows: list[tuple[str, str, str, str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        rows.append(
            (
                str(item.get("time", "")),
                str(item.get("level", "")),
                str(item.get("code", "")),
                str(item.get("message", "")),
                str(item.get("source", "")),
            ),
        )
    return rows
