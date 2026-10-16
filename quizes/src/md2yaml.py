"""<quiz_dir>/quiz.<lang>.md → <quiz_dir>/quiz.yaml (meta, questions, options, correct, topic, hints, explanation per language).

Usage: python quizes/src/md2yaml.py quizes/quiz-4-dagster                                  # every quiz.<lang>.md found
       python quizes/src/md2yaml.py quizes/quiz-3-dbt-review                               # test + reserve, review skipped
       python quizes/src/md2yaml.py quizes/quiz-3-dbt-review "## Переписанные вопросы"     # only that section (ru file only)

Each md may start with a YAML front matter (--- audience/purpose/goal/context/… ---); a question may have a «Тема: …»
line and several «Подсказка: …» lines (shown one by one, in the order written: from light to detailed). The marker words
(«Вопрос»/«Question», «Подсказка:»/«Hint:», …) are per language in settings.yml (lang.<code>). When several languages
exist, they must match: same question ids, difficulty, number of options and hints, same ✅ positions.
"""
import re
import sys
from pathlib import Path

import yaml

from settings import load_settings as load_merged, require

OPTION = re.compile(r"^\* (?:[А-ГA-D]\)|☑|☐)\s*(.*?)\s*$")
LANG_KEYS = ("question", "reserve", "hint", "explanation", "topic", "answers", "reserve_answers", "multi",
             "option_letters", "difficulties", "ui")


def load_settings(quiz_dir: Path) -> dict:
    cfg = load_merged(quiz_dir)
    require(cfg, "quiz.difficulties", "quiz.hint_difficulties", "quiz.meta_required", "lang")
    for code, L in cfg["lang"].items():
        require({**cfg, "lang": cfg["lang"]}, *(f"lang.{code}.{k}" for k in LANG_KEYS))
        assert len(L["difficulties"]) == len(cfg["quiz"]["difficulties"]), f"lang.{code}.difficulties: wrong length"
    return cfg


def head_re(L: dict) -> re.Pattern:
    """"Вопрос 4 🟨 применение · простой" or "**Вопрос 2 🟩 понимание.** Текст вопроса" (words from lang settings)."""
    return re.compile(
        rf"^(?:\*\*)?({L['question']}|{L['reserve']}) (\d+) (\S+) ([^\s.·*]+)\.?(?: · ([^\s.*]+))?\.?(?:\*\*)?[ \t]*(.*)$",
        re.M)


def split_front_matter(md: str) -> tuple[dict, str]:
    """({meta}, md without the front matter); {} when the md has none."""
    if not md.startswith("---\n"):
        return {}, md
    head, sep, rest = md[4:].partition("\n---\n")
    if not sep:
        raise ValueError("front matter is not closed with a --- line")
    return yaml.safe_load(head) or {}, rest.lstrip("\n")


def parse(md: str, L: dict) -> list[dict]:
    heads = list(head_re(L).finditer(md))
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
            elif l.startswith(L["hint"]):
                hints.append(l.removeprefix(L["hint"]).strip())
            elif l.startswith(L["topic"]):
                topic = l.removeprefix(L["topic"]).strip()
            elif l.startswith(L["explanation"]):
                explanation = l.removeprefix(L["explanation"]).strip()
            elif l and l != "---" and not options:
                text.append(l)
        n_correct = sum(o["correct"] for o in options)
        main = h.group(1) == L["question"]
        questions.append({
            "id": f"{'q' if main else 'r'}{h.group(2)}",
            "section": "main" if main else "reserve",
            "level": f"{h.group(3)} {h.group(4)}",
            "difficulty": h.group(5),
            "text": " ".join(text),
            "multi": L["multi"] in " ".join(text) or n_correct > 1,
            "topic": topic,
            "options": options,
            "hints": hints,
            "explanation": explanation,
        })
    return questions


def answer_key(q: dict, L: dict) -> str:
    if q["multi"]:
        return ", ".join(str(i + 1) for i, o in enumerate(q["options"]) if o["correct"])
    return L["option_letters"][next(i for i, o in enumerate(q["options"]) if o["correct"])]


def self_check(md: str, questions: list[dict], settings: dict, meta: dict, L: dict) -> None:
    quiz = settings["quiz"]
    assert questions, "no questions parsed"
    missing = [k for k in quiz["meta_required"] if not meta.get(k)]
    assert not missing, f"front matter lacks: {', '.join(missing)}"
    for q in questions:
        assert len(q["options"]) >= 2 and q["explanation"], f"{q['id']}: options/{L['explanation']} missing"
        assert any(o["correct"] for o in q["options"]), f"{q['id']}: no ✅"
        d = q["difficulty"]
        assert d is None or d in L["difficulties"], f"{q['id']}: unknown difficulty {d!r}"
        if d is not None and quiz["difficulties"][L["difficulties"].index(d)] in quiz["hint_difficulties"]:
            assert q["hints"], f"{q['id']}: «{d}» needs a «{L['hint']}» line (quiz.hint_difficulties)"
    for word, prefix in ((L["question"], L["answers"]), (L["reserve"], L["reserve_answers"])):
        m = re.search(rf'^(?:<a id="[^"]*"></a>)?{re.escape(prefix)} (.*)$', md, re.M)
        if not m:
            continue
        expected = {a.strip(): b.strip() for a, b in (p.split("—") for p in m.group(1).split("·"))}
        section = [q for q in questions if q["section"] == ("main" if word == L["question"] else "reserve")]
        assert len(section) == len(expected), f"{prefix} lists {len(expected)}, parsed {len(section)}"
        for q in section:
            got = answer_key(q, L)
            assert got == expected[q["id"][1:]], f"{q['id']}: ✅ gives {got}, {prefix} says {expected[q['id'][1:]]}"


def merge_langs(by_lang: dict[str, list[dict]], settings: dict) -> list[dict]:
    """One question list with language-dependent fields as {code: value}; fails when the languages disagree."""
    codes = list(by_lang)
    base, canon = by_lang[codes[0]], settings["quiz"]["difficulties"]
    out = []
    for i, q in enumerate(base):
        row = {c: by_lang[c][i] for c in codes if i < len(by_lang[c])}
        assert len(row) == len(codes), f"{q['id']}: missing in {', '.join(c for c in codes if c not in row)}"
        for c, x in row.items():
            same = (x["id"], x["section"], x["multi"], len(x["options"]), [o["correct"] for o in x["options"]],
                    len(x["hints"]), x["topic"] is None, x["level"].split()[0])
            ref = (q["id"], q["section"], q["multi"], len(q["options"]), [o["correct"] for o in q["options"]],
                   len(q["hints"]), q["topic"] is None, q["level"].split()[0])
            assert same == ref, f"{q['id']}: {c} differs from {codes[0]} (id/section/multi/options/✅/hints/topic/level)"
            dl = settings["lang"][c]["difficulties"]
            assert (x["difficulty"] is None) == (q["difficulty"] is None) and (
                x["difficulty"] is None or dl.index(x["difficulty"]) == settings["lang"][codes[0]]["difficulties"].index(q["difficulty"])
            ), f"{q['id']}: difficulty differs between {c} and {codes[0]}"
        d = q["difficulty"]
        out.append({
            "id": q["id"], "section": q["section"], "multi": q["multi"],
            "difficulty": None if d is None else canon[settings["lang"][codes[0]]["difficulties"].index(d)],
            "level": {c: row[c]["level"] for c in codes},
            "topic": {c: row[c]["topic"] for c in codes},
            "text": {c: row[c]["text"] for c in codes},
            "options": [{"text": {c: row[c]["options"][j]["text"] for c in codes}, "correct": o["correct"]}
                        for j, o in enumerate(q["options"])],
            "hints": {c: row[c]["hints"] for c in codes},
            "explanation": {c: row[c]["explanation"] for c in codes},
        })
    return out


def main() -> None:
    quiz_dir = Path(sys.argv[1])
    section = sys.argv[2] if len(sys.argv) > 2 else None
    settings = load_settings(quiz_dir)
    codes = [c for c in settings["lang"] if (quiz_dir / f"quiz.{c}.md").exists()]
    if section:
        codes = codes[:1] if codes[:1] == ["ru"] else sys.exit(f"{quiz_dir}: a section can only be taken from quiz.ru.md")
    if not codes:
        sys.exit(f"{quiz_dir}: no quiz.<lang>.md ({', '.join(settings['lang'])}) found")
    by_lang, titles, metas = {}, {}, {}
    for c in codes:
        src, L = quiz_dir / f"quiz.{c}.md", settings["lang"][c]
        meta, md = split_front_matter(src.read_text(encoding="utf-8"))
        titles[c], metas[c] = md.splitlines()[0].lstrip("# ").strip(), meta
        if section:
            start = md.find(f"\n{section}\n")
            if start < 0:
                sys.exit(f"{src}: heading {section!r} not found")
            md = re.split(r"\n## ", md[start + len(section) + 2:], maxsplit=1)[0]
        else:
            # the test itself ends where a "# " heading (e.g. the review) starts
            md = re.split(r"\n# ", md, maxsplit=1)[0]
        by_lang[c] = parse(md, L)
        try:
            self_check(md, by_lang[c], settings, meta, L)
        except AssertionError as e:
            sys.exit(f"{src}: {e}")
    try:
        questions = merge_langs(by_lang, settings)
    except AssertionError as e:
        sys.exit(f"{quiz_dir}: {e}")
    out = quiz_dir / "quiz.yaml"
    out.write_text(
        yaml.safe_dump({"langs": codes, "title": titles, "meta": metas, "questions": questions},
                       allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    print(f"{out}: {len(questions)} questions, languages {', '.join(codes)}, self-check OK")


if __name__ == "__main__":
    main()
