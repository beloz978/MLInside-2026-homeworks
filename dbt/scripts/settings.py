"""Строгое чтение settings.yml: нет секции/ключа — ValueError с именем ключа и файлом (без дефолтов).

Другой проект (напр. Dagster/) переиспользует скрипты, указав свой файл: `--settings <проект>/scripts/settings.yml`
(или `use(path)` из кода). Раскладка проекта: `<проект>/scripts/settings.yml`, `<проект>/config/`, `<проект>/data/`.
"""
from __future__ import annotations

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("settings.yml")   # bootstrap: файл самого dbt/; подменяется через use()


def use(path: str | Path) -> None:
    global FILE
    f = Path(path).expanduser().resolve()
    if not f.is_file():
        raise ValueError(f"нет файла настроек {f} — укажите существующий путь в --settings")
    FILE = f


def use_from_argv(argv: list[str], flag: str = "--settings") -> None:
    """Выбрать файл настроек по `--settings X` / `--settings=X` до чтения секций (разбор argparse идёт позже)."""
    for i, a in enumerate(argv):
        if a == flag and i + 1 < len(argv):
            return use(argv[i + 1])
        if a.startswith(flag + "="):
            return use(a.split("=", 1)[1])


def root() -> Path:
    """Корень проекта текущего файла настроек (`<проект>/scripts/settings.yml` → `<проект>`)."""
    return FILE.parent.parent


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
