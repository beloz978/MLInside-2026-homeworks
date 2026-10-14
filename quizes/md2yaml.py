"""quizes/<name>.md → quizes/<name>.yaml (questions, options, correct, hint, explanation).

Usage: python quizes/md2yaml.py quizes/test-4-dagster.md
"""
import re
import sys
from pathlib import Path

import yaml

HEAD = re.compile(r"^(Вопрос|Резерв) (\d+) (\S+) (\S+)(?: · (\S+))?\s*$", re.M)
OPTION = re.compile(r"^\* (?:[А-Г]\)|☑|☐)\s*(.*?)\s*$")
ANSWERS = {"Вопрос": "Ответы:", "Резерв": "Ответы резерва:"}


def parse(md: str) -> list[dict]:
    heads = list(HEAD.finditer(md))
    questions = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        # body stops at the next "---" separator (answers line, reserve header)
        body = md[h.end():end].split("\n---", 1)[0]
        lines = [l.strip() for l in body.strip().splitlines()]
        text, options, hint, explanation = [], [], None, None
        for l in lines:
            if (m := OPTION.match(l)) and m.group(1):
                options.append({"text": m.group(1).replace("✅", "").strip(), "correct": "✅" in m.group(1)})
            elif l.startswith("Подсказка:"):
                hint = l.removeprefix("Подсказка:").strip()
            elif l.startswith("Разбор:"):
                explanation = l.removeprefix("Разбор:").strip()
            elif l and not options:
                text.append(l)
        n_correct = sum(o["correct"] for o in options)
        questions.append({
            "id": f"{'q' if h.group(1) == 'Вопрос' else 'r'}{h.group(2)}",
            "section": "main" if h.group(1) == "Вопрос" else "reserve",
            "level": f"{h.group(3)} {h.group(4)}",
            "difficulty": h.group(5),
            "text": " ".join(text),
            "multi": "Несколько вариантов" in " ".join(text) or n_correct > 1,
            "options": options,
            "hint": hint,
            "explanation": explanation,
        })
    return questions


def answer_key(q: dict) -> str:
    if q["multi"]:
        return ", ".join(str(i + 1) for i, o in enumerate(q["options"]) if o["correct"])
    return "АБВГ"[next(i for i, o in enumerate(q["options"]) if o["correct"])]


def self_check(md: str, questions: list[dict]) -> None:
    for word, prefix in ANSWERS.items():
        m = re.search(rf"^{prefix} (.*)$", md, re.M)
        if not m:
            continue
        expected = {a.strip(): b.strip() for a, b in (p.split("—") for p in m.group(1).split("·"))}
        section = [q for q in questions if q["section"] == ("main" if word == "Вопрос" else "reserve")]
        assert len(section) == len(expected), f"{prefix} lists {len(expected)}, parsed {len(section)}"
        for q in section:
            assert len(q["options"]) >= 2 and q["explanation"], f"{q['id']}: options/Разбор missing"
            got = answer_key(q)
            assert got == expected[q["id"][1:]], f"{q['id']}: ✅ gives {got}, {prefix} says {expected[q['id'][1:]]}"


def main() -> None:
    src = Path(sys.argv[1])
    md = src.read_text(encoding="utf-8")
    questions = parse(md)
    self_check(md, questions)
    out = src.with_suffix(".yaml")
    title = md.splitlines()[0].strip()
    out.write_text(
        yaml.safe_dump({"title": title, "questions": questions}, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"{out}: {len(questions)} questions, self-check OK")


if __name__ == "__main__":
    main()
