#!/usr/bin/env python3
"""Проверка окружения: инструменты, Python-зависимости, переменные из .env и пути."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import load_env  # noqa: E402

load_env()
bad = 0


def line(ok: bool | None, label: str, detail: str = "") -> None:
    global bad
    mark = {True: "OK  ", False: "FAIL", None: "skip"}[ok]
    bad += ok is False
    print(f"[{mark}] {label:<26} {detail}")


print("== Инструменты ==")
line(sys.version_info >= (3, 10), "python >= 3.10", sys.version.split()[0])
for tool, required in (("make", True), ("uv", True), ("just", False), ("direnv", False), ("git", False)):
    path = shutil.which(tool)
    line(True if path else (False if required else None), tool, path or ("не найден" + ("" if required else " (не обязателен)")))

print("\n== Python-пакеты (venv) ==")
for mod, pkg in (("duckdb", "duckdb"), ("kagglehub", "kagglehub"), ("yaml", "pyyaml"), ("dbt", "dbt-core")):
    ok = importlib.util.find_spec(mod) is not None
    line(ok, pkg, "" if ok else "выполните: make setup")

print("\n== Переменные .env ==")
need = ["HW_DBT_PROJECT_DIR", "HW_DBT_PROFILES_DIR", "OLIST_DUCKDB_PATH"]
for name in need + ["OLIST_CSV_DIR", "HW_DBT_PROFILE", "HW_DBT_TARGETS", "HW_DBT_TARGET", "CONTROL_FIGURES_JSON"]:
    v = os.environ.get(name)
    line(bool(v) if name in need else None if not v else True, name, v or "(пусто)")

print("\n== Пути ==")
def p(name: str) -> Path | None:
    v = os.environ.get(name)
    return (ROOT / v).resolve() if v else None

proj, prof, cf = p("HW_DBT_PROJECT_DIR"), p("HW_DBT_PROFILES_DIR"), p("CONTROL_FIGURES_JSON")
line(bool(proj and (proj / "dbt_project.yml").exists()), "dbt_project.yml", str(proj))
line(bool(prof and (prof / "profiles.yml").exists()), "profiles.yml", str(prof))
line(bool(cf and cf.exists()), "control_figures.json", str(cf))

print("\nГотово." if not bad else f"\nПроблем: {bad}. Исправьте и повторите `just doctor`.")
raise SystemExit(1 if bad else 0)
