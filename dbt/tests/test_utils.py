import json
import os
import stat
from pathlib import Path

import pytest

from utils import ask, choose, close, read_json, resolve_path, update_env_file, yesno


def test_resolve_path(tmp_path, monkeypatch):
    assert resolve_path("a/b", tmp_path) == tmp_path / "a/b"
    assert resolve_path(str(tmp_path / "x"), Path("/nope")) == tmp_path / "x"
    monkeypatch.setenv("HOME", str(tmp_path))
    assert resolve_path("~/x", Path("/nope")) == tmp_path / "x"


def test_read_json(tmp_path):
    assert read_json(tmp_path / "missing.json") == {}
    f = tmp_path / "a.json"
    f.write_text(json.dumps({"k": "я"}), encoding="utf-8")
    assert read_json(f) == {"k": "я"}


@pytest.mark.parametrize("a,b,rel,abs_,expected", [
    (100.0, 100.4, 0.005, 0.0, True),
    (100.0, 101.0, 0.005, 0.0, False),
    (0, 0.4, 0, 0.5, True),        # абсолютный допуск перекрывает нулевой относительный
    (None, 1, 0.1, 0.0, False),
    (1, None, 0.1, 0.0, False),
])
def test_close(a, b, rel, abs_, expected):
    assert close(a, b, rel, abs_) is expected


def test_update_env_file_creates_with_header(tmp_path):
    f = tmp_path / ".env"
    update_env_file(f, {"A": "1"}, "# head")
    assert f.read_text() == "# head\nA=1\n"
    assert not (tmp_path / ".env.bak").exists()


def test_update_env_file_updates_keeps_comments_and_backs_up(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# c\nA=1\nB=2\n", encoding="utf-8")
    update_env_file(f, {"A": "9", "C": "3"})
    assert f.read_text() == "# c\nA=9\nB=2\nC=3\n"
    assert (tmp_path / ".env.bak").read_text() == "# c\nA=1\nB=2\n"


@pytest.mark.skipif(os.name != "posix", reason="chmod только на posix")
def test_update_env_file_local_is_private(tmp_path):
    f = tmp_path / ".env.local"
    update_env_file(f, {"GH_TOKEN": "x"})
    assert stat.S_IMODE(f.stat().st_mode) == 0o600


def test_prompts_non_interactive_return_defaults():
    assert ask("q", "d", ni=True) == "d"
    assert yesno("q", False, ni=True) is False
    assert choose("q", [("a", "A"), ("b", "B")], default=1, ni=True) == "b"


def test_ask_default_on_empty_and_eof(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ask("q", "d") == "d"

    def eof(_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert ask("q", "d") == "d"


@pytest.mark.parametrize("answer,default,expected", [("", True, True), ("", False, False), ("д", False, True),
                                                      ("Yes", False, True), ("н", True, False)])
def test_yesno(monkeypatch, answer, default, expected):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert yesno("q", default) is expected


@pytest.mark.parametrize("answer,expected", [("2", "b"), ("", "a"), ("9", "a"), ("x", "a")])
def test_choose(monkeypatch, capsys, answer, expected):
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert choose("q", [("a", "A"), ("b", "B")]) == expected
