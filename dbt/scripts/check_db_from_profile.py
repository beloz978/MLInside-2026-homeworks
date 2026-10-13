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
import re
import socket
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import load_env  # noqa: E402
from settings import section  # noqa: E402

load_env()
S = section("check_db_from_profile")

ENV_RE = re.compile(r"""\{\{\s*env_var\(\s*['"]([^'"]+)['"]\s*(?:,\s*['"]([^'"]*)['"]\s*)?\)\s*(?:\|\s*(as_\w+)\s*)?\}\}""")


def render(value):
    """Подставляет env_var(...) в строках; as_number/as_bool/as_native приводит типы."""
    if isinstance(value, dict):
        return {k: render(v) for k, v in value.items()}
    if isinstance(value, list):
        return [render(v) for v in value]
    if not isinstance(value, str):
        return value

    missing = []

    def sub(m):
        name, default = m.group(1), m.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        missing.append(name)
        return ""

    out = ENV_RE.sub(sub, value)
    if missing:
        raise KeyError(f"не задана переменная окружения: {', '.join(missing)}")
    if ENV_RE.search(value) and value.strip().endswith(("as_number }}", "as_number}}")):
        try:
            return int(out)
        except ValueError:
            return float(out)
    return out


def tcp_ok(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "tcp ok"
    except OSError as e:
        return False, f"tcp {host}:{port} недоступен: {e}"


def check_duckdb(cfg: dict, base: Path) -> tuple[bool, str]:
    import duckdb

    path = str(cfg.get("path", ":memory:"))
    if path != ":memory:" and not path.startswith(("md:", "motherduck:")):
        p = Path(path)
        p = p if p.is_absolute() else (base / p)
        parent = p.parent
        if not parent.exists():
            return False, f"каталог для базы не существует: {parent}"
        path = str(p)
    con = duckdb.connect(path)
    try:
        con.execute("SELECT 1").fetchone()
    finally:
        con.close()
    return True, f"duckdb ok ({path})"


def check_postgres(cfg: dict, timeout: float) -> tuple[bool, str]:
    host, port = cfg.get("host", "localhost"), int(cfg.get("port", 5432))
    ok, msg = tcp_ok(host, port, timeout)
    if not ok:
        return False, msg
    kw = dict(host=host, port=port, user=cfg.get("user"), password=cfg.get("password"),
              dbname=cfg.get("dbname") or cfg.get("database"), connect_timeout=int(timeout))
    try:
        import psycopg2

        con = psycopg2.connect(**kw)
    except ImportError:
        import psycopg

        con = psycopg.connect(**kw)
    try:
        cur = con.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        if cfg.get("schema"):
            cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (cfg["schema"],))
            if cur.fetchone() is None:
                return True, f"postgres ok, но схемы '{cfg['schema']}' нет (dbt создаст её сам, если хватит прав)"
    finally:
        con.close()
    return True, f"postgres ok ({host}:{port}/{kw['dbname']})"


def check_clickhouse(cfg: dict, timeout: float) -> tuple[bool, str]:
    host = cfg.get("host", "localhost")
    port = int(cfg.get("port", 8123 if not cfg.get("secure") else 8443))
    ok, msg = tcp_ok(host, port, timeout)
    if not ok:
        return False, msg
    user, password = cfg.get("user", "default"), cfg.get("password", "")
    db = cfg.get("schema") or cfg.get("database") or "default"
    # dbt-clickhouse по умолчанию ходит по HTTP (8123/8443); native 9000/9440 — через clickhouse-driver
    if port in (9000, 9440):
        from clickhouse_driver import Client

        c = Client(host=host, port=port, user=user, password=password, secure=bool(cfg.get("secure")),
                   connect_timeout=int(timeout))
        c.execute("SELECT 1")
        return True, f"clickhouse(native) ok ({host}:{port})"
    import clickhouse_connect

    c = clickhouse_connect.get_client(host=host, port=port, username=user, password=password,
                                      secure=bool(cfg.get("secure")), connect_timeout=int(timeout))
    c.query("SELECT 1")
    ver = c.server_version
    c.close()
    return True, f"clickhouse(http) ok ({host}:{port}, v{ver}, db={db})"


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
        t0 = time.time()
        try:
            cfg = render(outputs[t])
            typ = cfg.get("type")
            if typ == "duckdb":
                ok, msg = check_duckdb(cfg, pdir)
            elif typ == "postgres":
                ok, msg = check_postgres(cfg, args.timeout)
            elif typ == "clickhouse":
                ok, msg = check_clickhouse(cfg, args.timeout)
            else:
                ok, msg = False, f"тип адаптера '{typ}' не поддерживается скриптом"
        except ImportError as e:
            typ, ok, msg = outputs[t].get("type"), False, f"нет драйвера: {e.name} (pip install)"
        except Exception as e:  # noqa: BLE001 — нужен читаемый вердикт, а не трейс
            typ, ok = outputs[t].get("type"), False
            msg = f"{type(e).__name__}: {str(e)[:200]}".replace(str(outputs[t].get("password", "\0")), "***")
        results.append({"target": t, "type": typ, "ok": ok, "message": msg, "ms": int((time.time() - t0) * 1000)})

    if args.json:
        print(json.dumps({"profile": name, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"[{'OK ' if r['ok'] else 'FAIL'}] {r['target']:<12} {r['type'] or '?':<11} {r['ms']:>5} ms  {r['message']}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
