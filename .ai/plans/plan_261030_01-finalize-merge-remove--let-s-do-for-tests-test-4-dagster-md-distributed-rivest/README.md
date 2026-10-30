# Plan: finalize, merge and remove all possible (MLInside-2026-homeworks)

## Context
Запрос пользователя: «finalyze, merge & remove all possible». PR #1–#8 уже squash-смёрджены в `origin/main` (`4dbe17a`),
осталось убрать хвосты и не потерять уникальное. Read-only инвентаризация (агент `repo-open-branches-finalyzer`, 2026-10-30)
показала, что смёрджить новое нужно ровно одно (handoff по этапу 5 Dagster), остальное удаляется после сохранения уникального.
Отдельная проблема: эталон `Dagster-HW-MLI-26` потерян вместе с worktree `quizes-main` (см. память
`project_dagster-reference-staging`); его пересборка из транскрипта возможна (все 32 Write и Edit-правки есть в
`~/.claude/projects/…quizes-main/3a1fe342-….jsonl`) и вынесена в отдельный шаг **после** уборки и после ответа пользователя.

Не трогать (чужое/пользовательское): `Dagster/Makefile` (modified, `run: setup ready check`), `.ai/PLAN.md`, `.ai/tasks/`, `.recyclebin/`.

## Что смёрджить
| Что | Статус | Действие |
|---|---|---|
| `9fec47e` (висячий; `Dagster/PLAN.md` §15, handoff этапа 5) | не в main, ни одной ветки, под угрозой gc | `git branch keep/dagster-plan-stage5 9fec47e` → ветка `docs/dagster-stage5-handoff` от `origin/main`, `git cherry-pick 9fec47e` (merge-tree: CLEAN) → push → PR → merge |
| `docs/test-4-dagster-questions` | всё содержимое в main (squash), кроме 2 файлов | см. ниже: сохранить и снять |
| `feat/make-ux` | заменена #8 (`feat/make-ux-port`); слияние = конфликты в 19 файлах | **не мёрджить**, снять |

Push/PR/merge делает пользователь в Terminal.app: в сессии `gh` падает на TLS (x509 -26276), токены `hnkovr`/`dataengy` в keychain
невалидны, у bg-воркера нет DNS. Готовлю скрипт `.tmp/finalize-*.sh` (аккаунт `beloz978` — владелец origin), как раньше.

## Что удалить (в этом порядке, после согласия)
1. **Сохранить:** `git branch keep/dagster-plan-stage5 9fec47e` (после этого gc не страшен).
2. **Сохранить уникальное из `test-4-dagster` вне репо** (каталог выбирает пользователь; не `.recyclebin/`):
   `.ai/WiP/HANDOFF-261029-mlinside-landing.md`, `quizes/.bak/test-4-dagster.md.bak1`, `.tmp/merge-pr5.command`
   — либо `git tag archive/docs-test-4-a922594 a922594` (файлы 2 и 3 игнорируются git, только копия).
3. `git worktree remove .claude/worktrees/test-4-dagster` и `git branch -D docs/test-4-dagster-questions` (`-D`: squash не предок).
4. `make-ux`: `git worktree unlock` → `git worktree remove` → `git branch -D feat/make-ux` (опционально сначала `git tag archive/make-ux-97a14c7 97a14c7`).
   Блокировка («не удалять до коммита») выполнена: tip закоммичен, дерево чистое. Игнорируемые `dbt/config/.env`, `.env.bak` —
   меньше и старше копий в main (содержимое не читалось).
5. `rm -r .claude/worktrees/test-3-dbt` (незарегистрированный каталог: пустой `.cc-writes` и `.idea/workspace.xml`).
6. Удалённые ссылки: `git fetch dataengy --prune`; опционально `git push dataengy --delete fix/wizard-abs-paths` (одна правка remote).
7. Проверка PR из нормального терминала: `GH_TOKEN=$(gh auth token --user beloz978) gh pr list --repo beloz978/MLInside-2026-homeworks --state all`.

Порядок жёсткий: 1 → 2 → остальное. Шаги 3–6 необратимы, поэтому идут только после сохранений.

## После уборки (отдельным решением пользователя)
Эталон Dagster: сначала Finder/Time Machine на `quizes-main`/`Dagster-HW-MLI-26`; если нет — пересборка (replay Write/Edit из транскрипта +
`dbt/olist` из `~/gi/@dataengy/dbt-hw-MLI-26` с правками из §13 + `uv lock`), сразу в `~/gi/@dataengy/` (bg-сессия туда писать не может →
собрать в `.claude/worktrees/` и закоммитить в ветку, пользователь переносит), затем этап 5 (dlt + ML). Скилл `save-handoff-and-ship`
написать заново с правилом «не удалять worktree с уникальными игнорируемыми данными».

## Verification
- `git branch -a`, `git worktree list`: остались `main` (+ `keep/…` и/или `docs/dagster-stage5-handoff` до merge).
- `git show origin/main:Dagster/PLAN.md | grep '^## 15'` — после merge PR.
- `git cat-file -t 9fec47e` и `git branch --contains 9fec47e` — ветка `keep/…` существует.
- Файлы из шага 2 на месте до выполнения шага 3 (`ls`, `cmp`).
- `git status`: `Dagster/Makefile`, `.ai/PLAN.md`, `.ai/tasks/`, `.recyclebin/` без изменений.

## Не проверено
Состояние PR на GitHub (gh недоступен), содержимое `.env` в `make-ux`, живость владельца блокировки `make-ux`.
