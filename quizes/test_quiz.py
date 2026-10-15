"""Keypress tests for quiz.py: uv run --with questionary --with pyyaml --with pytest pytest quizes/test_quiz.py"""
import sys
from pathlib import Path

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

sys.path.insert(0, str(Path(__file__).parent))
import quiz  # noqa: E402

SETTINGS = {"hint_difficulties": ["средний"], "hint_position": "after", "hint_key": "h"}
SINGLE = {"text": "Q?", "level": "🟨", "difficulty": "средний", "multi": False, "hint": "подумай",
          "explanation": "e", "options": [{"text": t, "correct": t == "b"} for t in "abcd"]}
MULTI = {**SINGLE, "multi": True, "options": [{"text": t, "correct": t in "ac"} for t in "abcd"]}


def run(q, keys, settings=SETTINGS):
    with create_pipe_input() as inp:
        inp.send_text(keys)
        return quiz.ask(q, 1, 1, settings, input=inp, output=DummyOutput())


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
