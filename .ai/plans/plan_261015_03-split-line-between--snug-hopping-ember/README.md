# Plan: `---` split line between question and options in test-4

## Context
In `quizes/test-4-dagster.md` each question starts with a header carrying its complexity
(`Вопрос N 🟩 понимание · простой|средний|сложный`). The user wants a visual split line (`---`)
between the question text and the answer options, for all 20 questions (10 main + 10 reserve).

Catch: `quizes/md2yaml.py:parse` cuts a question body at the first `\n---`
(it uses that to stop at the "Ответы:" / "Резерв вопросов" separators), so a naive `---` would drop all options.

## Format (decided)
```
Вопрос 2 🟩 понимание · простой
Зачем ассету принимать ресурс…

---

* А) …
* Б) … ✅
```
Blank lines on both sides, otherwise Markdown renders the text above as a setext H2 heading.

## Changes
1. `quizes/md2yaml.py` (`parse`):
   - split regex `r"\n---|\n## "` → `r"\n---(?!\s*\*)|\n## "`. A `---` followed by an option line is not a body terminator; the separators before "Ответы:" and "Резерв вопросов" still are.
   - in the line loop, skip a `---` line, so it does not end up in `text`.
2. `quizes/test-4-dagster.md`: before the first option of every question, insert `---` with a blank line each side. One-off Python regex: `\n\n(?=\* (?:[А-Г]\)|☑|☐))` → `\n\n---\n\n`, first match per block only, header-to-header.
   Do not touch the existing `---` lines at 5 / 122 / 126 / 240.
3. `quizes/README.md`, section "Формат теста": one line saying that a `---` between the question and the options is required/expected.
4. Add a small test for the new parse rule (project convention: `quizes/test_quiz.py`): a question with `---` before the options parses with all options and without `---` in `text`.
5. Regenerate `quizes/test-4-dagster.yaml` (`make quiz-yaml 4`).

## Out of scope
- `test-3-dbt-review.md` (a review document, a different format) — not touched.
- The `AD quizes/FORMAT.md` entry in git status (staged add, deleted in the working tree) — not touched.

## Verification
- `make quiz-yaml 4`: self-check OK, 20 questions, and `git diff quizes/test-4-dagster.yaml` is empty (the data must not change).
- `make quiz-test`: green, including the new test.
- `grep -c '^---$' quizes/test-4-dagster.md` = 4 + 20 = 24.
- Quick look at one question in `make quiz 4` (options render, hint key still works).

## Git
Branch `docs/test-4-dagster-questions` (current). Conventional commit `docs(quizes): split line between question and options`; push/PR only after the user confirms.
