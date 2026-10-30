# План: разобрать `#todo`/`#fixme` из вывода `make setup … make check`

## Context

Вы прогнали всю цепочку из `MANUAL.md` (`make setup → wizard → seeds → ready → check`) и пометили
в выводе, что поправить. Сквозных причин три:

1. **Остатки Justfile.** `just doctor`, `just check-hw`, `just wizard` печатаются в подсказках, но Justfile в репо нет
   (в `Makefile` только `setup wizard seeds ready check`).
2. **Расхождение wizard ↔ doctor ↔ check_hw.** doctor требует `OLIST_DUCKDB_PATH` (FAIL «пусто»),
   а wizard его не пишет; `check_hw.py` при этом сам подставляет умолчание `.tmp/olist.duckdb`.
   В `doctor.py` остался отладочный код (`RO0T`, `cf = RO0T`), из-за него путь к `control_figures.json`
   считается от родителя репозитория (`…/MLInside-2026-homeworks/data/…`, а файл лежит в `dbt/data/`).
3. **Сырой вывод.** Нет цветов и эмодзи в doctor, нет пояснений к ошибкам, пути относительные, нет проверки PR/профиля.

Цель: каждый пункт ниже закрывает конкретную пометку. Ветка: `docs/merge-manual-config` (уже текущая, worktree не нужен).

## Правки по пометкам

| # | Пометка | Что сделать | Файл |
|---|---------|-------------|------|
| 1 | пустые строки-разделители между командами; запуск каждой команды с новой строки (`echo  # split-line`) | **Переиспользуем существующую цель `run`** (`setup wizard seeds ready check`), расширяем её, новых целей не заводим: рецепт из `@$(MAKE) --no-print-directory <шаг>` + `@echo` между шагами, `run` добавить в `.PHONY` и в `help`. В блоке «все команды в одной ячейке» (`README.md:10`) — `echo` между командами; в `MANUAL.md` (по шагам, с пояснениями) остаётся как есть, плюс строка «или всё сразу: `make run`» | `Makefile`, `README.md`, `MANUAL.md` |
| 2 | `setup`: идемпотентный venv (сейчас кривая строка `##\`[[ …`, вопрос «replace? yes») | Явная настройка в шапке Makefile: `VENV := .venv`; рецепт `@test -d $(VENV) \|\| uv venv $(VENV)` (+ `@echo "🆗 $(VENV) уже есть"`); `PY` строится от `$(VENV)`. Остальное без изменений. Работает в Git Bash/WSL, где и так нужен `make` | `Makefile` |
| 3 | `#fixme` путь `…/dbt/в/Users/…` | Это не баг поиска: введено `в/Users/…` (лишняя «в» от раскладки), путь стал относительным и приклеился к `ROOT`. Меняем только диагностику: в ошибке показывать введённую строку и «относительные пути считаются от `<ROOT>`»; пути в выводе печатать через `~` (хелпер `tilde(p)`) | `scripts/wizard.py` (`step_project`) |
| 4 | профиль `[olist]:` без «OK/нет» | После ввода имени проверять, что оно есть в `profiles.yml` верхним ключом (`yaml.safe_load`): `✅ профиль olist найден` / `❌ профиля X нет, есть: a, b` | `scripts/wizard.py` |
| 5 | уточнить `gh CLI` | `✅ GitHub CLI (gh) найден, вход выполнен` | `scripts/wizard.py:94` |
| 6 | полный URL репо; ошибка при нет доступа / нет PR | После ввода репо и номера PR: печатать `https://github.com/<repo>`, затем `gh_api.api(/repos/<repo>)` + `gh_api.find_pr` (временно выставив `HW_GH_PR`). Результат: `✅ доступ есть, PR #N <url>` / `⚠️ PR не найдены в <url>` / `❌ нет доступа к <url> (HTTP 404)`. Ошибка не прерывает мастер (шаг GitHub можно пропустить) | `scripts/wizard.py` (`step_github`) |
| 7 | абсолютные пути вместо относительных | `HW_DBT_PROJECT_DIR` / `HW_DBT_PROFILES_DIR` писать как `str(p.resolve())`; `rel()` остаётся только для показа «найдено рядом». Резолв `ROOT / v` в doctor/check_hw с абсолютными путями уже работает | `scripts/wizard.py` (`step_project`) |
| 8 | печатать полный путь `config/.env` | `✅ Готово: <ENV_DIR/.env> обновлён (бэкап: <…>.bak)`; то же для `.env.local` | `scripts/wizard.py:246` |
| 9 | `just doctor` / `just check-hw` → make | Использовать **уже существующие** `make ready` и `make check` (отдельный `make doctor` не нужен — `ready` и есть doctor + проверка СУБД). Заменить в `wizard.py:253`, `doctor.py:61`, `check_hw.py:16,490`, `gh_api.py:118`, `.env.example` (`just wizard` → `make wizard`; `just check-dbt` не трогаем — аналога в make нет) | перечисленные |
| 10 | `OLIST_DUCKDB_PATH (пусто)` FAIL | **Умолчания хранятся явно в настройках, а не неявно в коде.** Новая секция `settings.yml` → `env_defaults` (`OLIST_DUCKDB_PATH: .tmp/olist.duckdb`, `CONTROL_FIGURES_JSON: data/control_figures.json`, `HW_DBT_PROFILE: olist`, `HW_DBT_TARGETS: duckdb`) — единственный источник. wizard **явно записывает** эти ключи в `config/.env` (абсолютные пути; существующее значение не затирает — у вас уже `data/olist.duckdb`); doctor читает их из `.env` строго; `check_hw.pth(name, default)` теряет литералы `".tmp/olist.duckdb"` / `"data/control_figures.json"` и берёт значение из `env_defaults` (тот же ключ, ту же секцию). Значения в `config/.env.example` синхронизировать | `scripts/settings.yml`, `scripts/wizard.py`, `scripts/check_hw.py`, `config/.env.example` |
| 11 | строка с `control_figures.json` (`RO0T`) | Удалить `RO0T`, `cf = RO0T` и закомментированный `##?`; `CONTROL_FIGURES_JSON` перенести в `env_required`, проверять `p("CONTROL_FIGURES_JSON")` с подписью `control_figures.json` | `scripts/doctor.py`, `scripts/settings.yml` |
| 12 | эмодзи у статусов; подсветка проблемы; комментарии к FAIL | В `line()`: `OK→✅ OK`, `FAIL→❌ FAIL`, `skip→🆗 skip` (набор как в `check_hw.EMO`). FAIL-строка красная/жирная ANSI, только если `sys.stdout.isatty()` и нет `NO_COLOR`. Подсказки по именам вынести в `settings.yml` → `doctor.hints` (напр. `OLIST_DUCKDB_PATH: "задаётся мастером: make wizard"`, пакеты: `make setup`) и печатать под FAIL | `scripts/doctor.py`, `scripts/settings.yml` |
| 13 | пояснение к `make: *** [ready] Error 1` | Итоговая строка doctor: `❌ Проблем: N. Исправьте пункты FAIL выше и повторите make ready (ошибка make ниже — просто код возврата 1)`. Саму ошибку make не подавляем: она нужна, чтобы `run` останавливался | `scripts/doctor.py` |

## Что НЕ делаю

- Остальной «старый» хардкод `check_hw.py` (кроме двух путей из п. 10) не трогаю — в бэклог.
- `Justfile` не создаю — студенческий минимум остаётся на `make`.
- Конец вывода `make check` (баллы «N из 10») в вашем сообщении обрезан на `dbt seed …`, поэтому его результат мне неизвестен; после правок прогоню `make check` сам.

## Проверка

1. `make setup` дважды подряд — без вопроса и ошибки, `.venv` один раз.
2. `printf '\n…' | .venv/bin/python scripts/wizard.py --non-interactive --project ../../../@dataengy/dbt --dry-run` — абсолютные пути, `OLIST_DUCKDB_PATH`/`CONTROL_FIGURES_JSON` в списке записи.
3. Интерактивно (вам, `! make wizard`): неверный путь → в ошибке видна введённая строка; репо без PR → `⚠️`; чужой/несуществующий репо → `❌ HTTP 404`.
4. `make ready` на чистом `.env` без `OLIST_DUCKDB_PATH` → красный FAIL + подсказка; после `make wizard` → `Готово.`, код 0.
5. `make check` до итоговой строки «Проект прошёл на N из 10 баллов».
6. `grep -rn "just " scripts README.md MANUAL.md config/.env.example` — остался только `just check-dbt`.
7. Скаляры: `python3 ~/.ai/skills/_scripts/utils/find_hardcoded_scalars.py scripts/wizard.py scripts/doctor.py --exit-nonzero-on-find`.

Коммиты (Conventional Commits, мелкие): `fix(make): idempotent venv`, `feat(wizard): verify profile/repo/PR, absolute paths`, `fix(doctor): control_figures path, emoji/color/hints`, `docs: make ready/check instead of just`. Push и PR — только после вашего подтверждения.
