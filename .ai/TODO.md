# TODO

Planned work, grouped by subproject; inside each section, sorted by priority (P0 → P3).

## quizes

<!-- scope: quizes/ (*.md tests, md→yaml generator, interactive runner) -->

- [x] **P2 · TODO-quiz-runner** (done 2026-10-15: `1de8290` md2yaml, `94cfb72` quiz.py + `make quiz`, `b99e17e` hints, `deb168d` hotkeys, `edc935c` `make quiz-yaml`/`quiz-test`) — interactive terminal quiz from `quizes/*.md`: md→yaml (options, ✅, «Разбор», hint), multi-select, on-demand hint, scoring +1/−1 (min 0). Stack: Python + questionary + PyYAML.
  - Plan: [plan_261015_01-interactive-quiz-runner](plans/plan_261015_01-interactive-quiz-runner--whick-package-lib-on-python-bash-nushell-happy-piglet/README.md) ([PLAN.md](plans/plan_261015_01-interactive-quiz-runner--whick-package-lib-on-python-bash-nushell-happy-piglet/PLAN.md))
  - Hints: `Подсказка:` line, required for the levels in `quizes/src/settings.yml` (`quiz.hint_difficulties`).


## Handoffs

- [ ] [2026-10-29] [P1] Resume from handoff: [HANDOFF-261029-mlinside-landing.md](WiP/HANDOFF-261029-mlinside-landing.md) — Handoff: MLInside branch landing (2026-10-29)
  Resume: `git -C /Users/user/gi/@beloz978/MLInside-2026-homeworks status --porcelain && git -C /Users/user/gi/@beloz978/MLInside-2026-homeworks branch -a`
