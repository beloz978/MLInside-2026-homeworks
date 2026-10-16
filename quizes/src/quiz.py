"""Interactive terminal quiz from quizes/<name>.yaml (made by md2yaml.py).

Usage: uv run --with questionary --with pyyaml python quizes/src/quiz.py quizes/quiz-4-dagster.yaml
Only the main section is asked; reserve questions are skipped.
Keys: digits 1–9 pick (single) or toggle (multi) an option, Enter answers, the hint key (quizes/src/settings.yml) shows the hint.
"""
import sys
from pathlib import Path

import questionary
import yaml
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from questionary.prompts.common import InquirerControl

SETTINGS = Path(__file__).with_name("settings.yml")
SHOW_HINT = object()  # returned by a prompt when the hint key is pressed


def load_settings() -> dict:
    quiz = yaml.safe_load(SETTINGS.read_text(encoding="utf-8"))["quiz"]
    missing = [k for k in ("hint_difficulties", "hint_position", "hint_key") if k not in quiz]
    if missing:
        raise ValueError(f"{SETTINGS}: quiz.{', quiz.'.join(missing)} not set")
    if quiz["hint_position"] not in ("before", "after"):
        raise ValueError(f"{SETTINGS}: quiz.hint_position must be before or after")
    return quiz


def score(q: dict, picked: list[int]) -> tuple[int, int]:
    """(got, max). Multi: +1 per correct pick, −1 per wrong pick, not below 0. Single: 1/0."""
    correct = {i for i, o in enumerate(q["options"]) if o["correct"]}
    if q["multi"]:
        return max(0, len(correct & set(picked)) - len(set(picked) - correct)), len(correct)
    return int(picked == [next(iter(correct))]), 1


def add_hotkeys(question: questionary.Question, multi: bool, hint_key: str | None) -> questionary.Question:
    """Digits 1–9 toggle (multi) or point at (single) an option; hint_key ends the prompt with SHOW_HINT."""
    app = question.application
    # ponytail: reaches into questionary 2.x internals (InquirerControl.pointed_at/selected_options); recheck on upgrade
    ic = next(c for c in app.layout.find_all_controls() if isinstance(c, InquirerControl))
    kb = KeyBindings()
    for i in range(min(9, ic.choice_count)):
        @kb.add(str(i + 1), eager=True)
        def _(event, i=i):
            ic.pointed_at = i
            if multi:
                value = ic.choices[i].value
                ic.selected_options.remove(value) if value in ic.selected_options else ic.selected_options.append(value)
    if hint_key:
        @kb.add(hint_key, eager=True)
        def _(event):
            event.app.erase_when_done = True  # the prompt is redrawn with the hint, don't leave this copy
            event.app.exit(result=SHOW_HINT)
    app.key_bindings = merge_key_bindings([app.key_bindings, kb])
    return question


def prompt(q: dict, hint_shown: bool, settings: dict, **io) -> object:
    hint = q.get("hint") if q.get("difficulty") in settings["hint_difficulties"] else None
    bullet = f"  • 💡 {hint}"
    message = q["text"]
    if hint and hint_shown:
        if settings["hint_position"] == "before":
            print(bullet)
        else:
            message = f"{message}\n{bullet}"
    keys = "цифры — " + ("отметить, пробел тоже" if q["multi"] else "выбрать") + ", Enter — ответить"
    if hint and not hint_shown:
        keys += f", {settings['hint_key']} — подсказка"
    choices = [questionary.Choice(f"{i + 1}) {o['text']}", value=i) for i, o in enumerate(q["options"])]
    factory = questionary.checkbox if q["multi"] else questionary.select
    question = factory(message, choices=choices, instruction=f"({keys})", **io)
    return add_hotkeys(question, q["multi"], settings["hint_key"] if hint and not hint_shown else None).unsafe_ask()


def ask(q: dict, n: int, total: int, settings: dict, **io) -> tuple[int, int]:
    print(f"\nВопрос {n}/{total} · {q['level']}" + (f" · {q['difficulty']}" if q.get("difficulty") else ""))
    answer = prompt(q, False, settings, **io)
    if answer is SHOW_HINT:
        answer = prompt(q, True, settings, **io)
    picked = answer if q["multi"] else [answer]
    got, best = score(q, picked)
    right = "; ".join(o["text"] for o in q["options"] if o["correct"])
    print(f"{'✅' if got == best else '❌'} {got}/{best}. Верно: {right}")
    if q.get("explanation"):
        print(f"Разбор: {q['explanation']}")
    return got, best


def main() -> None:
    data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
    questions = [q for q in data["questions"] if q.get("section", "main") == "main"]
    settings = load_settings()
    print(data.get("title", ""))
    got = best = 0
    try:
        for n, q in enumerate(questions, 1):
            g, b = ask(q, n, len(questions), settings)
            got, best = got + g, best + b
    except (KeyboardInterrupt, EOFError):
        print("\nПрервано.")
    print(f"\nИтог: {got} из {best}")


# self-check of the scoring rule
_m = {"multi": True, "options": [{"correct": c} for c in (True, True, False, True)]}
assert score(_m, [0, 1, 3]) == (3, 3) and score(_m, [0, 2]) == (0, 3) and score(_m, [2]) == (0, 3)
assert score({"multi": False, "options": [{"correct": False}, {"correct": True}]}, [1]) == (1, 1)

if __name__ == "__main__":
    main()
