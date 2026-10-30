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

## Plans

Session plans imported from `~/.claude/plans` (hardlinked `PLAN.md` + `PLAN.yml` + `README.md` under `plans/`).

- [ ] [20261014_01_todo-fixme-setup] [2026-10-14] [P2] План: разобрать `#todo`/`#fixme` из вывода `make setup … make check`
  Plan: [plan_261014_01-todo-fixme-setup--here-is-its-output-abundant-parasol](plans/plan_261014_01-todo-fixme-setup--here-is-its-output-abundant-parasol/README.md)
- [x] [20261013_01_move-env-requirements] (done: PR #1 `52dd3b0`) [2026-10-13] [P2] Plan: move env/requirements to dbt/config/, slim root README, backlog the MANUAL.md question
  Plan: [plan_261013_01-move-env-requirements--merge-dbt-manual-md-dbt-readme-md-precious-taco](plans/plan_261013_01-move-env-requirements--merge-dbt-manual-md-dbt-readme-md-precious-taco/README.md)
- [ ] [20261014_02_tests-test-3] [2026-10-14] [P2] План: чистовик вопросов в начало `tests/test-3-dbt-review.md`
  Plan: [plan_261014_02-tests-test-3--vivid-imagining-naur](plans/plan_261014_02-tests-test-3--vivid-imagining-naur/README.md)
- [ ] [20261008_01_v2-dagster-dlt] [2026-10-08] [P2] Plan v2: Dagster + dlt + dbt (PokeAPI -> DuckDB -> dbt models), dg layout
  Plan: [plan_261008_01-v2-dagster-dlt--cheeky-crafting-otter](plans/plan_261008_01-v2-dagster-dlt--cheeky-crafting-otter/README.md)
- [x] [20261015_01_hw-dbt-pro] (done: PR #4 `43c6d14`) [2026-10-15] [P2] План: абсолютные HW_DBT_PRO*_DIR + перезапуск проверки ДЗ
  Plan: [plan_261015_02-hw-dbt-pro--expressive-juggling-cloud](plans/plan_261015_02-hw-dbt-pro--expressive-juggling-cloud/README.md)
- [ ] [20261015_02_split-line-between] [2026-10-15] [P2] Plan: `---` split line between question and options in test-4
  Plan: [plan_261015_03-split-line-between--snug-hopping-ember](plans/plan_261015_03-split-line-between--snug-hopping-ember/README.md)
- [ ] [20261016_01_polish-run-output] [2026-10-16] [P2] Polish `make run` output (wizard / doctor / check_db)
  Plan: [plan_261016_01-polish-run-output--for-make-run-linked-stonebraker](plans/plan_261016_01-polish-run-output--for-make-run-linked-stonebraker/README.md)
- [ ] [20261030_01_finalize-merge-remove] [2026-10-30] [P2] Plan: finalize, merge and remove all possible (MLInside-2026-homeworks)
  Plan: [plan_261030_01-finalize-merge-remove--let-s-do-for-tests-test-4-dagster-md-distributed-rivest](plans/plan_261030_01-finalize-merge-remove--let-s-do-for-tests-test-4-dagster-md-distributed-rivest/README.md)
