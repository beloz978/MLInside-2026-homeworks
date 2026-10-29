# Interactive quiz runner for `quizes/*.md` — library choice + plan

## Context
Quizzes live in `quizes/*.md` (e.g. `quizes/test-4-dagster.md`): questions with ☑/☐ or А)–Г) options,
✅ marks the correct answer, a «Разбор» explanation follows each question, multi-answer questions score
+1 for each correct choice, −1 for each extra one, never below 0. Goal: generate `quizes/<name>.yaml`
(questions, options, correct, hint, explanation) from the md, then run it as an interactive terminal quiz
with multi-select and an on-demand hint.

## Library comparison (checked against current docs via Context7)
| Lang | Pick | Multi-select | Hint | YAML | Deps |
|---|---|---|---|---|---|
| **Python** | **questionary** (`/tmbo/questionary`) | `checkbox()`; Space toggles, `a` selects all, `i` inverts, `validate=`, `instruction=` | `Choice(description=…)` shows text for the highlighted option; a hint for the whole question = a `select` menu "Answer / 💡 Hint" | PyYAML | 1 pip package |
| Go | charmbracelet/huh | `NewMultiSelect[T]().Options(...).Limit(n)` | `Description` / `DescriptionFunc` (can change dynamically) | yaml.v3 | single compiled binary |
| Bash | charmbracelet/gum | `gum choose --no-limit` | `gum confirm "Show hint?"` + `gum style` | `yq` | 2 brew binaries; you write the parsing and scoring yourself |
| Nushell | built-in `input list --multi` (0.111+: Multi/Fuzzy-multi, `a` = toggle all, Ctrl+R = refine) | yes | via an extra `input list` menu | `open x.yaml`, built in | zero deps |

**Recommendation: Python + questionary + PyYAML.** The repo already has Python scripts (`dbt/scripts/`),
and Python also covers the hard part, md→yaml parsing. Nushell is the zero-dependency runner option, but
the md parser is awkward to write in it. huh only makes sense if you want a standalone binary for students.

## Steps (the smallest version that does the job)
1. `quizes/md2yaml.py <file.md>` → `<file>.yaml`. Split on `^Вопрос N`, options are `* ` lines,
   `✅` → `correct: true`, «Разбор:» → `explanation`, `multi` = the question text contains «Несколько вариантов» /
   has more than one ✅. Hints are not in the md yet: add a `Подсказка:` line to the md format (parse it if present) — **this needs the user's OK**.
   Schema per question: `{id, level, text, multi, options: [{text, correct}], hint, explanation}`.
2. `quizes/quiz.py <file.yaml>`: for each question, a `questionary.select` menu "Answer / 💡 Hint" (hint shown at most once),
   then `checkbox` (multi) or `select` (single), then show score + explanation; total at the end.
   Scoring: multi = max(0, correct_picked − wrong_picked); single = 1/0.
3. A small assert self-check of md2yaml on `test-4-dagster.md`: 10 main questions; correct answers match the «Ответы» line.
4. Note the two commands in `quizes/README.md`.

## Files
- new: `quizes/md2yaml.py`, `quizes/quiz.py`, generated `quizes/*.yaml`
- edit: `quizes/README.md` (format: optional `Подсказка:` line; how to run)

## Verification
- `uv run --with pyyaml python quizes/md2yaml.py quizes/test-4-dagster.md` → yaml, self-check passes
- `uv run --with questionary --with pyyaml python quizes/quiz.py quizes/test-4-dagster.yaml` → go through Q1 (multi) and Q2 (single), use a hint, check the score
