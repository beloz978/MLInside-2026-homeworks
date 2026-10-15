"""quizes/<name>.md → quizes/<name>.yaml (questions, options, correct, hint, explanation).

Usage: python quizes/md2yaml.py quizes/test-4-dagster.md
       python quizes/md2yaml.py quizes/test-3-dbt-review.md                            # test + reserve, review skipped
       python quizes/md2yaml.py quizes/test-3-dbt-review.md "## Переписанные вопросы"  # only that section
"""
import re
import sys
from pathlib import Path

import yaml

# "Вопрос 4 🟨 применение · простой" or "**Вопрос 2 🟩 понимание.** Текст вопроса"
HEAD = re.compile(
    r"^(?:\*\*)?(Вопрос|Резерв) (\d+) (\S+) ([^\s.·*]+)\.?(?: · ([^\s.*]+))?\.?(?:\*\*)?[ \t]*(.*)$", re.M
)
OPTION = re.compile(r"^\* (?:[А-Г]\)|☑|☐)\s*(.*?)\s*$")
ANSWERS = {"Вопрос": "Ответы:", "Резерв": "Ответы резерва:"}
SETTINGS = Path(__file__).with_name("settings.yml")


def load_settings() -> dict:
    quiz = yaml.safe_load(SETTINGS.read_text(encoding="utf-8"))["quiz"]
    missing = [k for k in ("difficulties", "hint_difficulties") if k not in quiz]
    if missing:
        raise ValueError(f"{SETTINGS}: quiz.{', quiz.'.join(missing)} not set")
    return quiz


def parse(md: str) -> list[dict]:
    heads = list(HEAD.finditer(md))
    questions = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        # body stops at the next "---" separator (answers line, reserve header) or "## " heading;
        # a "---" followed by an option is the question/options split line, not a terminator
        body = re.split(r"\n---(?!\s*\*)|\n## ", md[h.end():end], maxsplit=1)[0]
        lines = [l.strip() for l in body.strip().splitlines()]
        text, options, hint, explanation = [h.group(6)] if h.group(6) else [], [], None, None
        for l in lines:
            if (m := OPTION.match(l)) and m.group(1):
                options.append({"text": m.group(1).replace("✅", "").strip(), "correct": "✅" in m.group(1)})
            elif l.startswith("Подсказка:"):
                hint = l.removeprefix("Подсказка:").strip()
            elif l.startswith("Разбор:"):
                explanation = l.removeprefix("Разбор:").strip()
            elif l and l != "---" and not options:
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


def self_check(md: str, questions: list[dict], settings: dict) -> None:
    assert questions, "no questions parsed"
    for q in questions:
        assert len(q["options"]) >= 2 and q["explanation"], f"{q['id']}: options/Разбор missing"
        assert any(o["correct"] for o in q["options"]), f"{q['id']}: no ✅"
        d = q["difficulty"]
        assert d is None or d in settings["difficulties"], f"{q['id']}: unknown difficulty {d!r}"
        if d in settings["hint_difficulties"]:
            assert q["hint"], f"{q['id']}: «{d}» needs a «Подсказка:» line (quizes/settings.yml)"
    for word, prefix in ANSWERS.items():
        m = re.search(rf'^(?:<a id="[^"]*"></a>)?{prefix} (.*)$', md, re.M)
        if not m:
            continue
        expected = {a.strip(): b.strip() for a, b in (p.split("—") for p in m.group(1).split("·"))}
        section = [q for q in questions if q["section"] == ("main" if word == "Вопрос" else "reserve")]
        assert len(section) == len(expected), f"{prefix} lists {len(expected)}, parsed {len(section)}"
        for q in section:
            got = answer_key(q)
            assert got == expected[q["id"][1:]], f"{q['id']}: ✅ gives {got}, {prefix} says {expected[q['id'][1:]]}"


def main() -> None:
    src = Path(sys.argv[1])
    md = src.read_text(encoding="utf-8")
    title = md.splitlines()[0].lstrip("# ").strip()
    if len(sys.argv) > 2:
        heading = sys.argv[2]
        start = md.find(f"\n{heading}\n")
        if start < 0:
            sys.exit(f"{src}: heading {heading!r} not found")
        md = re.split(r"\n## ", md[start + len(heading) + 2:], maxsplit=1)[0]
    else:
        # the test itself ends where a "# " heading (e.g. the review) starts
        md = re.split(r"\n# ", md, maxsplit=1)[0]
    questions = parse(md)
    self_check(md, questions, load_settings())
    out = src.with_suffix(".yaml")
    out.write_text(
        yaml.safe_dump({"title": title, "questions": questions}, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"{out}: {len(questions)} questions, self-check OK")


if __name__ == "__main__":
    main()
