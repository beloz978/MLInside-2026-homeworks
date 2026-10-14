"""Interactive terminal quiz from quizes/<name>.yaml (made by md2yaml.py).

Usage: uv run --with questionary --with pyyaml python quizes/quiz.py quizes/test-4-dagster.yaml
Only the main section is asked; reserve questions are skipped.
"""
import sys

import questionary
import yaml

ANSWER, HINT = "Ответить", "💡 Подсказка"


def score(q: dict, picked: list[int]) -> tuple[int, int]:
    """(got, max). Multi: +1 per correct pick, −1 per wrong pick, not below 0. Single: 1/0."""
    correct = {i for i, o in enumerate(q["options"]) if o["correct"]}
    if q["multi"]:
        return max(0, len(correct & set(picked)) - len(set(picked) - correct)), len(correct)
    return int(picked == [next(iter(correct))]), 1


def ask(q: dict, n: int, total: int) -> tuple[int, int]:
    print(f"\nВопрос {n}/{total} · {q['level']}" + (f" · {q['difficulty']}" if q.get("difficulty") else ""))
    if q.get("hint") and questionary.select(q["text"], choices=[ANSWER, HINT]).unsafe_ask() == HINT:
        print(f"💡 {q['hint']}")
    choices = [questionary.Choice(o["text"], value=i) for i, o in enumerate(q["options"])]
    if q["multi"]:
        picked = questionary.checkbox(
            q["text"], choices=choices, instruction="(пробел — выбрать, Enter — ответить)"
        ).unsafe_ask()
    else:
        picked = [questionary.select(q["text"], choices=choices).unsafe_ask()]
    got, best = score(q, picked)
    right = "; ".join(o["text"] for o in q["options"] if o["correct"])
    print(f"{'✅' if got == best else '❌'} {got}/{best}. Верно: {right}")
    if q.get("explanation"):
        print(f"Разбор: {q['explanation']}")
    return got, best


def main() -> None:
    data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
    questions = [q for q in data["questions"] if q.get("section", "main") == "main"]
    print(data.get("title", ""))
    got = best = 0
    try:
        for n, q in enumerate(questions, 1):
            g, b = ask(q, n, len(questions))
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
