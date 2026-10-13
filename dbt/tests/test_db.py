import duckdb
import pytest

import db
from db import check_duckdb, check_target, render, table_ref, tcp_ok


def test_render_env_default_and_nesting(monkeypatch):
    monkeypatch.setenv("T_HOST", "h1")
    monkeypatch.delenv("T_PORT", raising=False)
    cfg = {"host": "{{ env_var('T_HOST') }}", "port": "{{ env_var('T_PORT', '5432') }}", "list": ["{{ env_var('T_HOST') }}", 1]}
    assert render(cfg) == {"host": "h1", "port": "5432", "list": ["h1", 1]}


def test_render_missing_var_names_it(monkeypatch):
    monkeypatch.delenv("T_NOPE", raising=False)
    with pytest.raises(KeyError, match="T_NOPE"):
        render("{{ env_var('T_NOPE') }}")


def test_render_as_number(monkeypatch):
    monkeypatch.setenv("T_N", "42")
    assert render("{{ env_var('T_N') | as_number }}") == 42
    monkeypatch.setenv("T_N", "1.5")
    assert render("{{ env_var('T_N') | as_number }}") == 1.5


def test_tcp_ok_true_and_false(monkeypatch):
    class Sock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(db.socket, "create_connection", lambda addr, timeout: Sock())
    assert tcp_ok("h", 1, 1.0) == (True, "tcp ok")

    def refuse(addr, timeout):
        raise ConnectionRefusedError("refused")

    monkeypatch.setattr(db.socket, "create_connection", refuse)
    ok, msg = tcp_ok("h", 1, 1.0)
    assert not ok and "h:1" in msg and "refused" in msg


def test_check_duckdb_file_memory_and_missing_dir(tmp_path):
    assert check_duckdb({"path": ":memory:"}, tmp_path)[0] is True
    ok, msg = check_duckdb({"path": "sub/x.duckdb"}, tmp_path)
    assert not ok and "не существует" in msg
    (tmp_path / "sub").mkdir()
    ok, msg = check_duckdb({"path": "sub/x.duckdb"}, tmp_path)
    assert ok and (tmp_path / "sub" / "x.duckdb").exists()


def test_table_ref_prefers_main_and_skips_raw():
    con = duckdb.connect(":memory:")
    con.execute("create schema raw; create schema s1")
    con.execute("create table raw.t(a int); create table s1.t(a int); create table main.t(a int)")
    assert table_ref(con, "t") == '"main"."t"'
    con.execute("drop table main.t")
    assert table_ref(con, "t") == '"s1"."t"'
    con.execute("drop table s1.t")
    assert table_ref(con, "t") is None


def test_check_target_duckdb_ok(tmp_path):
    r = check_target("dev", {"type": "duckdb", "path": ":memory:"}, tmp_path, 1.0)
    assert r["ok"] and r["type"] == "duckdb" and r["target"] == "dev" and isinstance(r["ms"], int)


def test_check_target_unsupported_type(tmp_path):
    r = check_target("x", {"type": "oracle"}, tmp_path, 1.0)
    assert not r["ok"] and "oracle" in r["message"]


def test_check_target_missing_env_is_reported_not_raised(tmp_path, monkeypatch):
    monkeypatch.delenv("T_NOPE", raising=False)
    r = check_target("x", {"type": "postgres", "host": "{{ env_var('T_NOPE') }}"}, tmp_path, 1.0)
    assert not r["ok"] and "T_NOPE" in r["message"]


def test_check_target_redacts_password(tmp_path, monkeypatch):
    monkeypatch.setenv("T_PW", "s3cret")

    def boom(cfg, timeout):
        raise RuntimeError(f"auth failed for {cfg['password']}")

    monkeypatch.setattr(db, "check_postgres", boom)
    r = check_target("pg", {"type": "postgres", "password": "{{ env_var('T_PW') }}"}, tmp_path, 1.0)
    assert not r["ok"] and "s3cret" not in r["message"] and "***" in r["message"]


def test_check_target_empty_password_does_not_mangle_message(tmp_path, monkeypatch):
    def boom(cfg, timeout):
        raise RuntimeError("down")

    monkeypatch.setattr(db, "check_postgres", boom)
    r = check_target("pg", {"type": "postgres", "password": ""}, tmp_path, 1.0)
    assert r["message"] == "RuntimeError: down"


def test_check_target_missing_driver(tmp_path, monkeypatch):
    def nodrv(cfg, timeout):
        raise ImportError("x", name="psycopg2")

    monkeypatch.setattr(db, "check_postgres", nodrv)
    r = check_target("pg", {"type": "postgres"}, tmp_path, 1.0)
    assert not r["ok"] and "psycopg2" in r["message"]
