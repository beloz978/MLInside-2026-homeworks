"""Проверки мастера (scripts/wizard.py) и настроек doctor. Запуск: `.venv/bin/python tests/test_wizard_doctor.py` или pytest.

Без сети и без записи файлов: GitHub подменён заглушкой, файлы — во временном каталоге.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import urllib.error
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import wizard  # noqa: E402
from envload import ROOT  # noqa: E402
from settings import section  # noqa: E402


class FakeGh:
    """Заглушка gh_api: mode = 404 | ok | none."""

    mode = "ok"

    @classmethod
    def api(cls, path, token):
        if cls.mode == "404":
            raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        return {}

    @classmethod
    def find_pr(cls, repo, token, project):
        if os.environ["HW_GH_PR"] == "x":
            raise ValueError
        return {"number": 7, "title": "T", "html_url": "https://github.com/o/r/pull/7"} if cls.mode == "ok" else None


def verify(mode: str, pr: str) -> str:
    FakeGh.mode = mode
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        wizard.verify_repo_pr(FakeGh, "o/r", pr, None, None)
    return buf.getvalue()


def test_verify_repo_pr_no_access():
    out = verify("404", "")
    assert "https://github.com/o/r" in out and "❌ нет доступа" in out and "HTTP 404" in out


def test_verify_repo_pr_found():
    assert "✅ PR #7" in verify("ok", "7")


def test_verify_repo_pr_not_found():
    assert "⚠️" in verify("none", "")


def test_verify_repo_pr_bad_number():
    assert "должен быть числом" in verify("ok", "x")


def test_verify_repo_pr_restores_env():
    os.environ.pop("HW_GH_PR", None)
    verify("ok", "7")
    assert "HW_GH_PR" not in os.environ
    os.environ["HW_GH_PR"] = "5"
    try:
        verify("ok", "7")
        assert os.environ["HW_GH_PR"] == "5"
    finally:
        del os.environ["HW_GH_PR"]


def test_tilde():
    assert wizard.tilde(Path.home() / "a" / "b") == "~/a/b"
    assert wizard.tilde(Path("/definitely/not/home")) == "/definitely/not/home"


def test_profile_names():
    with tempfile.TemporaryDirectory() as d:
        assert wizard.profile_names(Path(d)) is None
        (Path(d) / "profiles.yml").write_text("config: {x: 1}\nolist: {}\nother: {}\n", encoding="utf-8")
        assert wizard.profile_names(Path(d)) == ["olist", "other"]


def test_doctor_hints_cover_all_fail_keys():
    for path in (None, ROOT.parent / "Dagster" / "scripts" / "settings.yml"):   # dbt и Dagster — один doctor.py
        s = yaml.safe_load(path.read_text(encoding="utf-8"))["doctor"] if path else section("doctor")
        keys = {"python", "packages", "env", "data_files"} | {it["file"] for it in s["paths"]}
        keys |= {t["name"] for t in s["tools"] if t["required"]}
        for k in keys:
            assert s["hints"][k], (path, k)


def test_wizard_defaults_in_settings():
    w = section("wizard")
    for k in ("duckdb_path", "control_figures_json", "profile", "targets", "repo_url"):
        assert w[k], k
    assert w["repo_url"].format(repo="o/r") == "https://github.com/o/r"


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"✅ {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"❌ {name}: {type(e).__name__}: {e}")
    raise SystemExit(1 if failed else 0)
