#!/usr/bin/env python3
"""Проверка доступности СУБД по кредам из dbt profiles.yml.

Для каждого (или выбранного) target профиля:
  1) разбирает profiles.yml, подставляя {{ env_var('X', 'default') }};
  2) проверяет TCP-доступность хоста/порта (postgres, clickhouse);
  3) открывает соединение родным драйвером и выполняет `SELECT 1`
     (duckdb: файл/путь; postgres: psycopg2/psycopg; clickhouse: clickhouse-connect
      по HTTP или clickhouse-driver по native-порту).

Код возврата: 0 — все проверенные target доступны, 1 — есть недоступные, 2 — ошибка запуска.
Пароли в вывод не попадают.

Примеры:
    python check_db_from_profile.py --profiles-dir ./dbt --profile olist
    python check_db_from_profile.py --profiles-dir ./dbt --targets duckdb,postgres --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import check_target  # noqa: E402
from envload import load_env  # noqa: E402
from logger import target_line  # noqa: E402
from settings import section  # noqa: E402

load_env()
S = section("check_db_from_profile")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profiles-dir", default=os.environ.get("HW_DBT_PROFILES_DIR", "."),
                    help="каталог с profiles.yml (по умолчанию $HW_DBT_PROFILES_DIR или .)")
    ap.add_argument("--profile", default=os.environ.get("HW_DBT_PROFILE") or None,
                    help="имя профиля (по умолчанию $HW_DBT_PROFILE или единственный в файле)")
    ap.add_argument("--targets", default=os.environ.get("HW_DBT_TARGETS") or None,
                    help="target через запятую (по умолчанию $HW_DBT_TARGETS или все)")
    ap.add_argument("--timeout", type=float, default=S["timeout_s"])
    ap.add_argument("--json", action="store_true", help="машиночитаемый вывод")
    args = ap.parse_args()

    # Относительный OLIST_DUCKDB_PATH из .env считаем от корня репозитория (как и dbt-раннер),
    # а не от каталога profiles.yml.
    db_env = os.environ.get("OLIST_DUCKDB_PATH")
    if db_env and not os.path.isabs(db_env):
        os.environ["OLIST_DUCKDB_PATH"] = str(Path(__file__).resolve().parent.parent / db_env)

    pdir = Path(args.profiles_dir).resolve()
    pfile = pdir / "profiles.yml"
    if not pfile.exists():
        print(f"нет {pfile}", file=sys.stderr)
        return 2
    profiles = yaml.safe_load(pfile.read_text(encoding="utf-8")) or {}
    profiles = {k: v for k, v in profiles.items() if isinstance(v, dict) and "outputs" in v}
    name = args.profile or (next(iter(profiles)) if len(profiles) == 1 else None)
    if name is None or name not in profiles:
        print(f"укажите --profile, доступны: {', '.join(profiles) or '—'}", file=sys.stderr)
        return 2

    outputs = profiles[name]["outputs"]
    wanted = [t.strip() for t in args.targets.split(",")] if args.targets else list(outputs)
    results = []
    for t in wanted:
        if t not in outputs:
            results.append({"target": t, "type": None, "ok": False, "message": "target не найден в profiles.yml", "ms": 0})
            continue
        results.append(check_target(t, outputs[t], pdir, args.timeout))

    if args.json:
        print(json.dumps({"profile": name, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(target_line(r))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
