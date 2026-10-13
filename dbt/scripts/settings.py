"""Строгое чтение settings.yml: нет секции/ключа — ValueError с именем ключа и файлом (без дефолтов)."""
from __future__ import annotations

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("settings.yml")


def _wrap(path: str, v):
    if isinstance(v, dict):
        return Strict(path, v)
    return [_wrap(f"{path}[{i}]", x) for i, x in enumerate(v)] if isinstance(v, list) else v


class Strict(dict):
    def __init__(self, path: str, data: dict):
        super().__init__({k: _wrap(f"{path}.{k}".lstrip("."), v) for k, v in data.items()})
        self._path = path

    def __missing__(self, key: str):
        raise ValueError(f"нет ключа '{f'{self._path}.{key}'.lstrip('.')}' в {FILE} — добавьте его")


def section(name: str) -> Strict:
    return Strict("", yaml.safe_load(FILE.read_text(encoding="utf-8")) or {})[name]
