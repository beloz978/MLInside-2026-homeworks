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
PROMPT = quiz.load_settings(Path(__file__).parent.parent / "quiz-4-dagster")[2]["ru"]["prompt_failed"]
SETTINGS = {"hint_difficulties": ["средний"], "hint_position": "after", "hint_key": "h", "pause_key": "p", "ui": UI,
            "mode": "immediate", "hints_enabled": True, "prompt_failed": PROMPT, "title": "T", "meta": {"audience": "студенты", "goal": "цель"}}
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
    assert names == ["question_shown", "choose", "choose", "unchoose", "hint_shown", "answer", "prompt_generated"]
    assert [e.get("option") for e in ev if e["event"] in ("choose", "unchoose")] == [1, 2, 1]
    ans = next(e for e in ev if e["event"] == "answer")
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


def test_failed_question_gets_prompt_and_file(capsys):
    assert run(SINGLE, "3\r") == (0, 1)  # picked c, right is b
    out = capsys.readouterr().out
    assert "Промпт для ChatGPT" in out and "Я выбрал(а): 3) c" in out and "Правильный ответ: 2) b" in out
    assert "студенты" in out and "T»" in out
    ev = events()
    assert ev[-1]["event"] == "prompt_generated" and ev[-1]["file"].endswith("-prompts.md")
    text = (LOG.path.with_name(LOG.path.stem + "-prompts.md")).read_text(encoding="utf-8")
    assert "Вопрос:\nQ?" in text and text.count("```") == 2


def test_right_answer_has_no_prompt(capsys):
    assert run(SINGLE, "2\r") == (1, 1)
    assert "Промпт для ChatGPT" not in capsys.readouterr().out
    assert not LOG.path.with_name(LOG.path.stem + "-prompts.md").exists()


def test_exam_mode_prints_nothing_until_report(capsys):
    exam = {**SETTINGS, "mode": "exam"}
    results = []
    with create_pipe_input() as inp:
        inp.send_text("3\r")
        quiz.ask({**SINGLE, "topic": "Тема1"}, 1, 1, exam, LOG, results, input=inp, output=DummyOutput())
    before = capsys.readouterr().out
    assert "Верно" not in before and "Разбор" not in before and "Промпт" not in before and "Ответ принят" in before
    quiz.exam_report(results, exam)
    after = capsys.readouterr().out
    assert "❌ 0/1" in after and "Тема1" in after and "Верно: b" in after and "Я выбрал(а): 3) c" in after


def test_hints_can_be_disabled():
    assert run(SINGLE, "h2\r", {**SETTINGS, "hints_enabled": False}) == (1, 1)
    assert not [e for e in events() if e["event"] == "hint_shown"]


# ---- presets ----
import random  # noqa: E402

import presets as pr  # noqa: E402

QCFG = {"difficulties": ["простой", "средний", "сложный"]}
BASE_P = pr.load_presets(Path("/nonexistent"))["practice"]


def bq(i, section="main", difficulty="простой", topic="A", n_opts=3):
    return {"id": f"{'q' if section == 'main' else 'r'}{i}", "section": section, "difficulty": difficulty, "multi": False,
            "topic": {"ru": topic, "en": topic + "-en"} if topic else None,
            "options": [{"text": {"ru": str(j)}, "correct": j == 0} for j in range(n_opts)]}


QS = [bq(1, difficulty="сложный", topic="A"), bq(2, difficulty="простой", topic="B"), bq(3, difficulty="средний", topic="A"),
      bq(4, difficulty="простой", topic="B"), bq(5, "reserve", "сложный", "C"), bq(6, "reserve", "простой", None)]


def sel(**over):
    return [q["id"] for q in pr.select(QS, {**BASE_P, **over}, QCFG, random.Random(1))]


def test_preset_filters_and_orders():
    assert sel() == ["q1", "q2", "q3", "q4"]  # practice: main only, as is
    assert sel(order="asc") == ["q2", "q4", "q3", "q1"] and sel(order="desc") == ["q1", "q3", "q2", "q4"]
    assert sel(sections=["main", "reserve"], difficulty_min="средний") == ["q1", "q3", "r5"]
    assert sel(topics=["B"]) == ["q2", "q4"] and sel(topics=["A-en"]) == ["q1", "q3"]  # any language matches
    assert sel(topic_order="grouped") == ["q1", "q3", "q2", "q4"]
    assert sel(count=2) == ["q1", "q2"]


def test_preset_random_is_reproducible_by_seed():
    a = sel(count=2, pick="random", order="random")
    assert a == sel(count=2, pick="random", order="random") and len(a) == 2
    other = [q["id"] for q in pr.select(QS, {**BASE_P, "count": 2, "pick": "random", "order": "random"}, QCFG, random.Random(2))]
    assert set(a) <= {"q1", "q2", "q3", "q4"} and set(other) <= {"q1", "q2", "q3", "q4"}


def test_shuffle_options_keeps_correct_and_remembers_origin():
    (q, *_), = [pr.select(QS, {**BASE_P, "shuffle_options": True}, QCFG, random.Random(5))]
    assert sorted(o["orig"] for o in q["options"]) == [0, 1, 2]
    assert [o["orig"] for o in q["options"] if o["correct"]] == [0]


def test_preset_validation_names_preset_and_key():
    langs, topics = ["ru", "en"], {"A", "A-en"}
    pr.validate("ok", BASE_P, QCFG, langs, topics)
    for key, bad, msg in (("mode", "fast", "mode"), ("count", 0, "count"), ("order", "up", "order"), ("topics", ["Z"], "unknown"),
                          ("seed", "x", "seed"), ("hints", "yes", "hints"),
                          ("sections", [], "sections"), ("lang", "de", "lang")):
        with pytest.raises(ValueError, match=f"preset 'p'.*{msg}"):
            pr.validate("p", {**BASE_P, key: bad}, QCFG, langs, topics)
    with pytest.raises(ValueError, match="must not be harder"):
        pr.validate("p", {**BASE_P, "difficulty_min": "средний", "difficulty_max": "простой"}, QCFG, langs, topics)
    with pytest.raises(ValueError, match="keys not set: seed"):
        pr.validate("p", {k: v for k, v in BASE_P.items() if k != "seed"}, QCFG, langs, topics)
    with pytest.raises(ValueError, match="unknown keys: extra"):
        pr.validate("p", {**BASE_P, "extra": 1}, QCFG, langs, topics)
    with pytest.raises(ValueError, match="selects no questions"):
        pr.select(QS, {**BASE_P, "topics": ["B"], "difficulty_min": "средний"}, QCFG, random.Random(1))


def test_real_quiz_presets_are_valid():
    import yaml
    for d in ("quiz-3-dbt-review", "quiz-4-dagster"):
        qd = Path(__file__).parent.parent / d
        raw = yaml.safe_load((qd / "quiz.yaml").read_text(encoding="utf-8"))
        cfg = quiz.load_settings(qd)[0]
        topics = {t for q in raw["questions"] for t in (q.get("topic") or {}).values() if t}
        for name, p in pr.load_presets(qd).items():
            pr.validate(name, p, cfg, raw["langs"], topics)
            assert pr.select(raw["questions"], p, cfg, random.Random(0)), (d, name)
