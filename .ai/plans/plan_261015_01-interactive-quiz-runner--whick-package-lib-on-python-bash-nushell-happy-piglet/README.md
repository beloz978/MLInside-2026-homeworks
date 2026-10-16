# Interactive quiz runner for `quizes/*.md` — library choice + plan

> Imported plan — canonical source lives in `~/.claude/plans/whick-package-lib-on-python-bash-nushell-happy-piglet.md`.
> This directory is the project-side projection. `PLAN.md` and the source share
> inode `62089608`, so edits via either path stay in sync.

## TL;DR

Quizzes live in `quizes/*.md` (e.g. `quizes/test-4-dagster.md`): questions with ☑/☐ or А)–Г) options, ✅ marks the correct answer, a «Разбор» explanation follows each question, multi-answer questions score +1 for each correct choice, −1 for each extra one, never below 0. Goal: generate `quizes/<name>.yaml` (questions, options, correct, hint, explanation) from the md, then run it as an interactive terminal quiz with multi-select and an on-demand hint.

## Layout

| File | Role |
|---|---|
| [`PLAN.md`](PLAN.md) | Plan body (hardlink — same inode as the source plan) |
| [`PLAN.yml`](PLAN.yml) | Structured metadata: Origin, Todo, DoD, Jira refs |
| `README.md` | This file — human-readable summary + navigation |

## Origin

- **Source:** `/Users/user/.claude/plans/whick-package-lib-on-python-bash-nushell-happy-piglet.md`
- **Imported:** 2026-10-14T20:09:25Z
- **Project:** `/Users/user/gi/@beloz978/MLInside-2026-homeworks/.claude/worktrees/test-4-dagster`
- **Branch @ import:** `docs/test-4-dagster-questions` (`b99e17e`)
- **Session:** -

## Backlog

- [`TODO-quiz-runner`](../../TODO.md#quizes) in `.ai/TODO.md` → section `quizes`

## Linked Jira

_Not linked yet — run `/add-plan-as-jira-task`._

## Refresh

```bash
# Regenerate PLAN.yml.todo / PLAN.yml.dod from the latest PLAN.md body
just -f ~/.ai/skills/_catalog/agentic/skills/add-plan-to-project/Justfile \
    refresh-plan-dir dir="$(dirname "$0")"
```

<!-- plan-yml-info-start -->
# PLAN.yml info

> Rendered from `PLAN.yml` by `~/.ai/scripts/markdown/generate-md-from-yaml.py` (plan_yml schema). Edit `PLAN.yml` and re-run `just refresh-plan-dir` to update.

## Origin

- **Basename:** `whick-package-lib-on-python-bash-nushell-happy-piglet`
- **Source plan:** `/Users/user/.claude/plans/whick-package-lib-on-python-bash-nushell-happy-piglet.md`
- **Imported at:** 2026-10-14T20:09:25Z
- **Source mtime:** 2026-10-15T00:09:04
- **Project dir:** `/Users/user/gi/@beloz978/MLInside-2026-homeworks/.claude/worktrees/test-4-dagster`
- **Git branch:** `docs/test-4-dagster-questions`
- **Git commit:** `b99e17e`
- **Session:** -
- **Hardlink inode:** `62089608`

## Todo

_(no todo items)_

## DoD

- [ ] `uv run --with pyyaml python quizes/md2yaml.py quizes/test-4-dagster.md` → yaml, self-check passes
- [ ] `uv run --with questionary --with pyyaml python quizes/quiz.py quizes/test-4-dagster.yaml` → go through Q1 (multi) and Q2 (single), use a hint, check the score

## Jira refs

_Not linked yet — run `/add-plan-as-jira-task`._

<!-- plan-yml-info-end -->
