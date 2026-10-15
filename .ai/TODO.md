# TODO

Planned work, grouped by subproject; inside each section, sorted by priority (P0 → P3).

## Dagster

<!-- scope: Dagster/ (self-check toolchain), reference solution repo dataengy/Dagster-HW-MLI-26 -->

- [ ] **P2 · TODO-dagster-selfcheck** — self-check for the Dagster homework (`make check` → «N из 10», mirroring `dbt/`) plus the reference solution `~/gi/@dataengy/Dagster-HW-MLI-26` (not created yet).
  - Plan: [Dagster/PLAN.md](../Dagster/PLAN.md)

## quizes

<!-- scope: quizes/ (*.md tests, md→yaml generator, interactive runner) -->

- [x] **P2 · TODO-quiz-runner** (done 2026-10-15: `1de8290` md2yaml, `94cfb72` quiz.py + `make quiz`, `b99e17e` hints, `deb168d` hotkeys, `edc935c` `make quiz-yaml`/`quiz-test`) — interactive terminal quiz from `quizes/*.md`: md→yaml (options, ✅, «Разбор», hint), multi-select, on-demand hint, scoring +1/−1 (min 0). Stack: Python + questionary + PyYAML.
  - Plan: [plan_261015_01-interactive-quiz-runner](plans/plan_261015_01-interactive-quiz-runner--whick-package-lib-on-python-bash-nushell-happy-piglet/README.md) ([PLAN.md](plans/plan_261015_01-interactive-quiz-runner--whick-package-lib-on-python-bash-nushell-happy-piglet/PLAN.md))
  - Hints: `Подсказка:` line, required for the levels in `quizes/src/settings.yml` (`quiz.hint_difficulties`).
