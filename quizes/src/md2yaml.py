"""<quiz_dir>/quiz.ru.md → <quiz_dir>/quiz.yaml (meta, questions, options, correct, topic, hints, explanation).

The md may start with a YAML front matter (--- audience/purpose/goal/context/… ---); a question may have a «Тема: …»
line and several «Подсказка: …» lines (shown one by one, in the order written: from light to detailed).

Usage: python quizes/src/md2yaml.py quizes/quiz-4-dagster
       python quizes/src/md2yaml.py quizes/quiz-3-dbt-review                            # test + reserve, review skipped
       python quizes/src/md2yaml.py quizes/quiz-3-dbt-review "## Переписанные вопросы"  # only that section
"""
import re
import sys
from pathlib import Path

import yaml

from settings import load_settings as load_merged, require

# "Вопрос 4 🟨 применение · простой" or "**Вопрос 2 🟩 понимание.** Текст вопроса"
HEAD = re.compile(
    r"^(?:\*\*)?(Вопрос|Резерв) (\d+) (\S+) ([^\s.·*]+)\.?(?: · ([^\s.*]+))?\.?(?:\*\*)?[ \t]*(.*)$", re.M
)
OPTION = re.compile(r"^\* (?:[А-Г]\)|☑|☐)\s*(.*?)\s*$")
ANSWERS = {"Вопрос": "Ответы:", "Резерв": "Ответы резерва:"}


def load_settings(quiz_dir: Path) -> dict:
    cfg = load_merged(quiz_dir)
    require(cfg, "quiz.difficulties", "quiz.hint_difficulties", "quiz.meta_required")
    return cfg["quiz"]


def split_front_matter(md: str) -> tuple[dict, str]:
    """({meta}, md without the front matter); {} when the md has none."""
    if not md.startswith("---\n"):
        return {}, md
    head, sep, rest = md[4:].partition("\n---\n")
    if not sep:
        raise ValueError("front matter is not closed with a --- line")
    return yaml.safe_load(head) or {}, rest.lstrip("\n")


def parse(md: str) -> list[dict]:
    heads = list(HEAD.finditer(md))
    questions = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(md)
        # body stops at the next "---" separator (answers line, reserve header) or "## " heading;
        # a "---" followed by an option is the question/options split line, not a terminator
        body = re.split(r"\n---(?!\s*\*)|\n## ", md[h.end():end], maxsplit=1)[0]
        lines = [l.strip() for l in body.strip().splitlines()]
        text, options, hints, topic, explanation = [h.group(6)] if h.group(6) else [], [], [], None, None
        for l in lines:
            if (m := OPTION.match(l)) and m.group(1):
                options.append({"text": m.group(1).replace("✅", "").strip(), "correct": "✅" in m.group(1)})
            elif l.startswith("Подсказка:"):
                hints.append(l.removeprefix("Подсказка:").strip())
            elif l.startswith("Тема:"):
                topic = l.removeprefix("Тема:").strip()
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
            "topic": topic,
            "options": options,
            "hints": hints,
            "explanation": explanation,
        })
    return questions


def answer_key(q: dict) -> str:
    if q["multi"]:
        return ", ".join(str(i + 1) for i, o in enumerate(q["options"]) if o["correct"])
    return "АБВГ"[next(i for i, o in enumerate(q["options"]) if o["correct"])]


def self_check(md: str, questions: list[dict], settings: dict, meta: dict) -> None:
    assert questions, "no questions parsed"
    missing = [k for k in settings["meta_required"] if not meta.get(k)]
    assert not missing, f"front matter lacks: {', '.join(missing)}"
    for q in questions:
        assert len(q["options"]) >= 2 and q["explanation"], f"{q['id']}: options/Разбор missing"
        assert any(o["correct"] for o in q["options"]), f"{q['id']}: no ✅"
        d = q["difficulty"]
        assert d is None or d in settings["difficulties"], f"{q['id']}: unknown difficulty {d!r}"
        if d in settings["hint_difficulties"]:
            assert q["hints"], f"{q['id']}: «{d}» needs a «Подсказка:» line (quiz.hint_difficulties)"
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
    quiz_dir = Path(sys.argv[1])
    src = quiz_dir / "quiz.ru.md"
    meta, md = split_front_matter(src.read_text(encoding="utf-8"))
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
    self_check(md, questions, load_settings(quiz_dir), meta)
    out = quiz_dir / "quiz.yaml"
    out.write_text(
        yaml.safe_dump({"title": title, "meta": meta, "questions": questions}, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"{out}: {len(questions)} questions, self-check OK")


if __name__ == "__main__":
    main()
