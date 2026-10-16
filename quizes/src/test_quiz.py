"""Keypress tests for quiz.py: uv run --with questionary --with pyyaml --with pytest pytest quizes/src/test_quiz.py"""
import json
import sys
from pathlib import Path

import pytest

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

sys.path.insert(0, str(Path(__file__).parent))
import quiz  # noqa: E402

SETTINGS = {"hint_difficulties": ["средний"], "hint_position": "after", "hint_key": "h", "pause_key": "p"}
SINGLE = {"text": "Q?", "level": "🟨", "difficulty": "средний", "multi": False, "hint": "подумай",
          "explanation": "e", "options": [{"text": t, "correct": t == "b"} for t in "abcd"]}
MULTI = {**SINGLE, "multi": True, "options": [{"text": t, "correct": t in "ac"} for t in "abcd"]}


@pytest.fixture(autouse=True)
def log(tmp_path):
    global LOG
    LOG = quiz.Log(tmp_path / "run.jsonl")
    return LOG


def run(q, keys, settings=SETTINGS):
    with create_pipe_input() as inp:
        inp.send_text(keys)
        return quiz.ask(q, 1, 1, settings, LOG, input=inp, output=DummyOutput())


def events():
    return [json.loads(line) for line in LOG.path.read_text(encoding="utf-8").splitlines()]


def test_single_digit_picks_option():
    assert run(SINGLE, "2\r") == (1, 1)
    assert run(SINGLE, "3\r") == (0, 1)


def test_multi_digits_toggle():
    assert run(MULTI, "13\r") == (2, 2)
    assert run(MULTI, "133\r") == (1, 2)  # 3 toggled back off
    assert run(MULTI, "12\r") == (0, 2)   # one right, one wrong


def test_hint_key_then_answer(capsys):
    assert run(SINGLE, "h2\r", {**SETTINGS, "hint_position": "before"}) == (1, 1)
    assert "• 💡 подумай" in capsys.readouterr().out


def test_hint_key_ignored_for_simple_question():
    # «простой» is not in hint_difficulties: "h" is not bound, so it is not an answer either
    assert run({**SINGLE, "difficulty": "простой"}, "h2\r") == (1, 1)


def test_md2yaml_split_line_before_options():
    import md2yaml
    md = "Вопрос 1 🟨 применение · простой\nЧто?\n\n---\n\n* А) a\n* Б) b ✅\n\nРазбор: e\n\n---\n\nОтветы: 1 — Б\n"
    (q,) = md2yaml.parse(md)
    assert q["text"] == "Что?" and [o["text"] for o in q["options"]] == ["a", "b"]


def test_log_choose_unchoose_hint_answer():
    assert run(MULTI, "232h\r") == (1, 2)  # 3 (correct «c») stays chosen across the hint redraw
    ev = events()
    names = [e["event"] for e in ev if e["event"] != "move"]
    assert names == ["question_shown", "choose", "choose", "unchoose", "hint_shown", "answer"]
    assert [e.get("option") for e in ev if e["event"] in ("choose", "unchoose")] == [1, 2, 1]
    ans = ev[-1]
    assert ans["picked"] == [2] and ans["hint_used"] and ans["n_toggles"] == 3
    assert [e["ms"] for e in ev] == sorted(e["ms"] for e in ev)


def test_log_pause_keeps_selection():
    assert run(SINGLE, "2px\r") == (1, 1)
    names = [e["event"] for e in events()]
    assert names[-3:] == ["pause", "resume", "answer"] and events()[-1]["paused_ms"] >= 0


def test_identity_env_requires_var(monkeypatch):
    monkeypatch.delenv("QUIZ_USER_TEST", raising=False)
    with pytest.raises(ValueError, match="QUIZ_USER_TEST"):
        quiz.identity({"identity": "env", "identity_env": "QUIZ_USER_TEST"})
    monkeypatch.setenv("QUIZ_USER_TEST", "anna")
    assert quiz.identity({"identity": "env", "identity_env": "QUIZ_USER_TEST"})["user"] == "anna"


def test_settings_file_is_valid():
    quiz_cfg, log_cfg = quiz.load_settings()
    assert log_cfg["identity"] in quiz.IDENTITY_MODES and quiz_cfg["pause_key"]
