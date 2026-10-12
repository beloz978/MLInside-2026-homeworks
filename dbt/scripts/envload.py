"""Мини-загрузчик .env и .env.local (без внешних зависимостей).

Уже заданные в окружении переменные не перезаписываются: shell/direnv/just главнее файлов.
Порядок: окружение > .env.local > .env.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().removeprefix("export ").strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k] = v
    return out


def load_env(root: Path = ROOT) -> None:
    for name in (".env.local", ".env"):          # .env.local читаем первым → он приоритетнее .env
        for k, v in parse_env(root / name).items():
            if k not in os.environ or os.environ[k] == "":
                os.environ[k] = v
