#!/usr/bin/env python3
"""Проверка окружения: инструменты, Python-зависимости, переменные из .env и пути."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RO0T = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import load_env  # noqa: E402
from settings import section  # noqa: E402

load_env()
S = section("doctor")
bad = 0


def line(ok: bool | None, label: str, detail: str = "") -> None:
    global bad
    mark = {True: "OK  ", False: "FAIL", None: "skip"}[ok]
    bad += ok is False
    print(f"[{mark}] {label:<26} {detail}")


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
def p(name: str) -> Path | None:
    v = os.environ.get(name)
    return (ROOT / v).resolve() if v else None

proj, prof, cf = p("HW_DBT_PROJECT_DIR"), p("HW_DBT_PROFILES_DIR"), p("CONTROL_FIGURES_JSON")
cf = RO0T
line(bool(proj and (proj / "dbt_project.yml").exists()), "dbt_project.yml", str(proj))
line(bool(prof and (prof / "profiles.yml").exists()), "profiles.yml", str(prof))
##? line(bool(cf and cf.exists()), "control_figures.json", str(cf))
line(bool(cf and cf.exists()), f"{RO0T}/data/control_figures.json", str(cf))# + '; ' + os.getcwd())

print("\nГотово." if not bad else f"\nПроблем: {bad}. Исправьте и повторите `just doctor`.")
raise SystemExit(1 if bad else 0)
