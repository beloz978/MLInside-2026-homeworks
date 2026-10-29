#!/usr/bin/env python3
"""Проверка окружения: инструменты, Python-зависимости, переменные из .env и пути.

    python scripts/doctor.py                                  # dbt/
    python scripts/doctor.py --settings ../Dagster/scripts/settings.yml   # другой проект: свои списки и config/
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import settings  # noqa: E402
from envload import load_env  # noqa: E402
from logger import Checks  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--settings", help="settings.yml проекта (по умолчанию — этого dbt/)")
settings.use_from_argv(sys.argv)
ap.parse_args()
ROOT = settings.root()
load_env(ROOT / "config")
S = settings.section("doctor")
checks = Checks()
line = checks.line


print("== Инструменты ==")
pmin = tuple(S["python_min"])
line(sys.version_info >= pmin, "python >= " + ".".join(map(str, pmin)), sys.version.split()[0])
for t in S["tools"]:
    tool, required = t["name"], t["required"]
    path = shutil.which(tool)
    line(True if path else (False if required else None), tool, path or ("не найден" + ("" if required else " (не обязателен)")))

print("\n== Python-пакеты (venv) ==")
for pk in S["python_packages"]:
    mod, pkg = pk["module"], pk["package"]
    ok = importlib.util.find_spec(mod) is not None
    line(ok, pkg, "" if ok else "выполните: make setup")

print("\n== Переменные .env ==")
need = S["env_required"]
for name in need + S["env_optional"]:
    v = os.environ.get(name)
    line(bool(v) if name in need else None if not v else True, name, v or "(пусто)")

print("\n== Пути ==")
for it in S["paths"]:
    v = os.environ.get(it["env"])
    d = (ROOT / v).resolve() if v else None
    line(bool(d and (d / it["file"]).exists()), it["file"], str(d))
for name in S["data_files"]:
    line((ROOT / "data" / name).exists(), f"data/{name}")

print("\nГотово." if not checks.bad else f"\nПроблем: {checks.bad}. Исправьте и повторите `just doctor`.")
raise SystemExit(1 if checks.bad else 0)
