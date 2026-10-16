"""Keypress tests for quiz.py: uv run --with questionary --with pyyaml --with pytest pytest quizes/src/test_quiz.py"""
import json
import sys
from pathlib import Path

import pytest

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

sys.path.insert(0, str(Path(__file__).parent))
import md2yaml  # noqa: E402
import quiz  # noqa: E402

LRU = md2yaml.load_settings(Path(__file__).parent.parent / "quiz-4-dagster")["lang"]["ru"]

QUIZ_DIR = Path(__file__).parent.parent / "quiz-4-dagster"
UI = quiz.load_settings(Path(__file__).parent.parent / "quiz-4-dagster")[2]["ru"]["ui"]
SETTINGS = {"hint_difficulties": ["средний"], "hint_position": "after", "hint_key": "h", "pause_key": "p", "ui": UI}
SINGLE = {"text": "Q?", "level": "🟨", "difficulty": "средний", "multi": False, "hints": ["подумай"],
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
    (q,) = md2yaml.parse(md, LRU)
    assert q["text"] == "Что?" and [o["text"] for o in q["options"]] == ["a", "b"]


def test_log_choose_unchoose_hint_answer():
    assert run(MULTI, "232h\r") == (1, 2)  # 3 (correct «c») stays chosen across the hint redraw
    ev = events()
    names = [e["event"] for e in ev if e["event"] != "move"]
    assert names == ["question_shown", "choose", "choose", "unchoose", "hint_shown", "answer"]
    assert [e.get("option") for e in ev if e["event"] in ("choose", "unchoose")] == [1, 2, 1]
    ans = ev[-1]
    assert ans["picked"] == [2] and ans["hints_used"] == 1 and ans["n_toggles"] == 3
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
    quiz_cfg, log_cfg, lang_cfg = quiz.load_settings(Path(__file__).parent.parent / "quiz-4-dagster")
    assert log_cfg["identity"] in quiz.IDENTITY_MODES and quiz_cfg["pause_key"] and set(lang_cfg) >= {"ru", "en"}


def test_settings_override_wins_and_missing_errors(tmp_path):
    import settings
    (tmp_path / "settings.yml").write_text("quiz:\n  hint_key: x\nlog:\n  dir: mylogs\n", encoding="utf-8")
    cfg = settings.load_settings(tmp_path)
    assert cfg["quiz"]["hint_key"] == "x" and cfg["quiz"]["pause_key"] == "p"  # override wins, rest from base
    assert cfg["log"]["dir"] == "mylogs" and cfg["log"]["identity"] == "os_git"
    with pytest.raises(ValueError, match="quiz.nope"):
        settings.require(cfg, "quiz.nope")
    with pytest.raises(ValueError, match="settings.yml missing"):
        settings.load_settings(tmp_path / "absent")


def test_several_hints_come_one_by_one_in_order(capsys):
    q = {**SINGLE, "hints": ["легко", "подробно"]}
    assert run(q, "hh2\r", {**SETTINGS, "hint_position": "before"}) == (1, 1)
    out = capsys.readouterr().out
    assert out.index("1/2 легко") < out.index("2/2 подробно")
    hs = [e for e in events() if e["event"] == "hint_shown"]
    assert [(e["level"], e["of"]) for e in hs] == [(1, 2), (2, 2)]
    assert events()[-1]["hints_used"] == 2


def test_extra_hint_key_after_last_hint_is_ignored():
    assert run(SINGLE, "hh2\r") == (1, 1)  # one hint only: the second h is not bound
    assert [e["level"] for e in events() if e["event"] == "hint_shown"] == [1]


def test_front_matter_topic_and_hints_parse():
    import md2yaml
    meta, md = md2yaml.split_front_matter("---\naudience: a\ngoal: g\n---\n\nТест\n\nВопрос 1 🟨 применение · средний\nЧто?\n\n---\n\n* А) a\n* Б) b ✅\n\nТема: ref\n\nПодсказка: раз\n\nПодсказка: два\n\nРазбор: e\n")
    assert meta == {"audience": "a", "goal": "g"} and md.startswith("Тест")
    (q,) = md2yaml.parse(md, LRU)
    assert q["topic"] == "ref" and q["hints"] == ["раз", "два"]


def test_self_check_needs_meta_and_hint():
    q = {"id": "q1", "options": [{"text": "a", "correct": True}, {"text": "b", "correct": False}], "explanation": "e",
         "difficulty": "средний", "hints": ["h"], "section": "main", "multi": False}
    cfg = {"quiz": {"difficulties": ["простой", "средний", "сложный"], "hint_difficulties": ["средний"], "meta_required": ["goal"]}}
    with pytest.raises(AssertionError, match="front matter lacks: goal"):
        md2yaml.self_check("", [q], cfg, {}, LRU)
    with pytest.raises(AssertionError, match="needs a «Подсказка:»"):
        md2yaml.self_check("", [{**q, "hints": []}], cfg, {"goal": "g"}, LRU)
    md2yaml.self_check("", [q], cfg, {"goal": "g"}, LRU)


def test_ru_and_en_files_match_and_merge():
    cfg = md2yaml.load_settings(QUIZ_DIR)
    by = {}
    for c in ("ru", "en"):
        _, md = md2yaml.split_front_matter((QUIZ_DIR / f"quiz.{c}.md").read_text(encoding="utf-8"))
        by[c] = md2yaml.parse(md.split("\n# ")[0], cfg["lang"][c])
    qs = md2yaml.merge_langs(by, cfg)
    assert len(qs) == 20 and qs[0]["text"]["en"].startswith("What is true") and qs[1]["difficulty"] == "простой"
    by["en"][1]["options"][0]["correct"] = True  # a ✅ moved in one language only
    with pytest.raises(AssertionError, match="differs"):
        md2yaml.merge_langs(by, cfg)


def test_localize_picks_language_and_difficulty_name():
    import yaml
    raw = yaml.safe_load((QUIZ_DIR / "quiz.yaml").read_text(encoding="utf-8"))
    quiz_cfg, _, lang_cfg = quiz.load_settings(QUIZ_DIR)
    en = quiz.localize(raw, "en", quiz_cfg, lang_cfg["en"])
    q = en["questions"][1]
    assert q["difficulty"] == "простой" and q["difficulty_name"] == "easy" and q["hints"] == []
    assert q["options"][1]["text"].startswith("So the connection") and en["meta"]["goal"].startswith("The student")
    ru = quiz.localize(raw, "ru", quiz_cfg, lang_cfg["ru"])
    assert ru["questions"][1]["difficulty_name"] == "простой" and ru["title"].startswith("Тест 4")


def test_english_ui_strings(capsys):
    settings = {**SETTINGS, "ui": quiz.load_settings(QUIZ_DIR)[2]["en"]["ui"]}
    assert run(SINGLE, "2\r", settings) == (1, 1)
    out = capsys.readouterr().out
    assert "Question 1/1" in out and "Correct: b" in out and "Explanation: e" in out
