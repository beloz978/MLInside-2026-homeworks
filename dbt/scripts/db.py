"""Работа с СУБД: разбор env_var в profiles.yml, проверки доступности duckdb/postgres/clickhouse.

Без побочных эффектов при импорте: таймауты и креды приходят параметрами.
"""
from __future__ import annotations

import os
import re
import socket
import time
from pathlib import Path

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


def table_ref(con, name: str) -> str | None:
    """Квалифицированное имя таблицы в DuckDB (схема main в приоритете) или None."""
    r = con.execute("select table_schema from information_schema.tables where lower(table_name)=? "
                    "and table_schema not in ('information_schema','raw') order by (table_schema='main') desc limit 1",
                    [name]).fetchone()
    return f'"{r[0]}"."{name}"' if r else None


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


def check_target(name: str, output: dict, base: Path, timeout: float) -> dict:
    """Проверяет один output из profiles.yml → {target, type, ok, message, ms}. Пароль в message не попадает."""
    t0 = time.time()
    typ, cfg = output.get("type"), output
    try:
        cfg = render(output)
        typ = cfg.get("type")
        if typ == "duckdb":
            ok, msg = check_duckdb(cfg, base)
        elif typ == "postgres":
            ok, msg = check_postgres(cfg, timeout)
        elif typ == "clickhouse":
            ok, msg = check_clickhouse(cfg, timeout)
        else:
            ok, msg = False, f"тип адаптера '{typ}' не поддерживается скриптом"
    except ImportError as e:
        ok, msg = False, f"нет драйвера: {e.name} (pip install)"
    except Exception as e:  # noqa: BLE001 — нужен читаемый вердикт, а не трейс
        ok, msg = False, f"{type(e).__name__}: {str(e)[:200]}"
        pw = str(cfg.get("password") or "")
        if pw:
            msg = msg.replace(pw, "***")
    return {"target": name, "type": typ, "ok": ok, "message": msg, "ms": int((time.time() - t0) * 1000)}
