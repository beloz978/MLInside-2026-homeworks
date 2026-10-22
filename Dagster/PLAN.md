# План: самопроверка ДЗ по Dagster и эталонное решение

Бэклог: [.ai/TODO.md → TODO-dagster-selfcheck](../.ai/TODO.md#dagster) · Задание: [ДЗ/ДЗ_Dagster_Olist.md](ДЗ/ДЗ_Dagster_Olist.md) · Образец: [`dbt/`](../dbt/README.md)

## 1. Цель и границы

- **Студенту:** в `Dagster/` тот же путь, что в `dbt/`: `make setup → wizard → data → ready → check`. Итог — оценка **«N из 10»** по [таблице оценок](ДЗ/ДЗ_Dagster_Olist.md#критерии-оценки) (6–7 / 8–9 / 10).
- **Автору курса:** эталонное решение в отдельном репозитории `~/gi/@dataengy/Dagster-HW-MLI-26` (`dataengy/Dagster-HW-MLI-26`; пушить под аккаунтом `dataengy`). На нём `make check` даёт 10 из 10, на пустом шаблоне — 0.
- **Вне рамок:** оценка качества модели (в задании не оценивается), Dagster+ / облачный деплой, ClickHouse как обязательное хранилище (основное — DuckDB, как в `dbt/`).
- **Перед стартом** студент проходит [тест 4 «Dagster»](../quizes/test-4-dagster.md): `make quiz 4` из корня.

## 2. Что переиспользуем из `dbt/`

| Из `dbt/` | Как используем в `Dagster/` |
|---|---|
| `Makefile` (setup, wizard, seeds, ready, check, test, run) | та же схема целей; `seeds` → `data` |
| `scripts/envload.py`, `settings.py`, `logger.py`, `utils.py` | импорт через `sys.path` из `../dbt/scripts`, без копий |
| `scripts/gh_api.py` (`pr_report`: PR, скриншот, версия, ссылка на CI, статус Actions) | как есть; в `settings.yml` — свои регексы версий (`dagster`, `dagster-dbt`) |
| `scripts/fetch_olist_seeds.py` | как есть, для данных уровня 6–9 (`dbt seed`) |
| `scripts/doctor.py` | как есть; списки пакетов и ключей `.env` — из `Dagster/scripts/settings.yml` (секция `doctor`) |
| `check_hw.py`: класс `Criterion` (подпроверки, балл только если все прошли), флаги `--no-run --no-gh --json --min` | та же модель; меняются сами проверки |
| `data/control_figures.json`, `raw_expectations.json` | те же 8 таблиц и row counts — для критерия 10 (`dlt`) |
| `config/.env.example` + `.env.local.example`, строгое чтение без дефолтов | та же схема (см. §3) |

`doctor.py` и `check_hw.py` принимают `--settings <проект>/scripts/settings.yml` (этап 0): корень проекта, `config/` и `data/` берутся от этого файла. Остаётся для этапа 2: `check_hw.py` dbt-специфичен целиком, поэтому `Criterion`/`Sub` и вывод отчёта нужно вынести в общий модуль, а не импортировать `check_hw` (импорт читает секцию `check_hw` и `data/hints.yaml`).

## 3. Структура `Dagster/`

```
Dagster/
  README.md  MANUAL.md  PLAN.md  Makefile
  config/  .env.example  .env.local.example  requirements.txt
  data/    hints.yaml               # подсказки к непройденным критериям
  scripts/ check_hw.py  inspect_defs.py  wizard.py  settings.yml  README.md
  tests/   conftest.py  test_check_hw.py  fixtures/{empty,tier7,tier9}/
  ДЗ/      ДЗ_Dagster_Olist.md
```

- **`config/.env.example`:** `HW_DAGSTER_PROJECT_DIR`, `HW_DAGSTER_MODULE` (или `HW_DAGSTER_WORKSPACE`), `HW_DBT_PROJECT_DIR`, `OLIST_CSV_DIR`, `OLIST_DUCKDB_PATH`, `DAGSTER_ENV`, `HW_GH_REPO`, `HW_GH_PR`.
- **`config/.env.local.example`:** `GH_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — значения пустые.
- **`config/requirements.txt`:** `dagster`, `dagster-webserver`, `dagster-dbt`, `dbt-core`, `dbt-duckdb`, `dagster-dlt`, `dlt[duckdb]`, `kagglehub`, `scikit-learn`, `pyyaml`, `pytest`. Версии — в [§10](#10-версии-этап-0).
- **`scripts/settings.yml`:** секции `check_hw` (уровни, пороги: минимум витрин 2, cron, имена групп), `inspect_defs` (таймауты), `doctor`, `wizard`, `gh_api` (регексы версий). Читается строго, отсутствующий ключ — ошибка с именем ключа.

## 4. Как проверять проект студента

- **Интроспекция без запуска** — `scripts/inspect_defs.py` запускается в venv студента:
  - грузит `Definitions` (через `dagster.components.load_defs`, `load_from_defs_folder` или модуль из `HW_DAGSTER_MODULE`);
  - пишет JSON: ассеты (ключ, группа, deps, kinds, `automation_condition`, freshness policy, `retry_policy`), asset checks (`blocking`), schedules (cron), sensors (тип / имя), resources, jobs.

  Без запуска данных это быстро, поэтому дёшево проверяются критерии 1–3, 5 и 7–8.
- **Материализация** (без `--no-run`): `dagster asset materialize -m <module> --select '*'` в изолированном `DAGSTER_HOME` (tmp). После этого:
  - через `DagsterInstance` читаем события материализаций и результаты checks;
  - затем через DuckDB по `OLIST_DUCKDB_PATH` сверяем row counts raw-таблиц с `raw_expectations.json` и витрины с `control_figures.json`.
- **Файлы репозитория:** `.pre-commit-config.yaml`, `.github/workflows/*.yml` (есть `dagster definitions validate` / `dg check defs` и `pytest`), `tests/` с `materialize_to_memory` / `materialize`.
- **GitHub** — `gh_api.pr_report`: PR, скриншоты в теле, версии пакетов, ссылка на успешный прогон CI. Сеть недоступна → в критерии ошибка, не падение (как в dbt).

## 5. Критерии «N из 10»

Каждый критерий даёт 1 балл, если прошли все его подпроверки. Пороги — 7 / 9 / 10, как в таблице задания.

| # | Критерий | Подпроверки |
|---|---|---|
| 1 | Определения грузятся | `inspect_defs` без ошибок; ≥1 ассет |
| 2 | Raw-слой | есть raw-ассеты (`dbt seed` или свой / `dlt`); все 8 таблиц Olist загружены, row counts совпадают |
| 3 | dbt в графе | dbt-модели — ассеты; staging + ≥2 витрины; lineage raw → staging → marts без разрывов (у каждого staging есть upstream среди raw) |
| 4 | dbt-тесты как checks | asset checks есть у dbt-ассетов; после материализации все зелёные; 2 витрины сходятся с `control_figures.json` |
| 5 | Расписание и запуск | `ScheduleDefinition` с ежедневным cron на граф/job; материализация из CLI успешна |
| 6 | Документация и PR | README с установкой/запуском; PR: версии `dagster`/`dagster-dbt`/`dbt-core`/адаптера, ≥1 скриншот |
| 7 | Automation + freshness | на витринах `automation_condition` (eager / on_cron); freshness policy хотя бы на одном ассете; секреты не в репо (поиск токенов по регексам из `settings.yml`) |
| 8 | Алерт + «Как устроен Dagster» | sensor на сбой (`run_failure_sensor` / `make_slack_on_run_failure_sensor`-аналог, Telegram-ресурс через `EnvVar`); ≥1 из: ресурсы по окружениям (`DAGSTER_ENV`), pytest для ассетов, retry + blocking check |
| 9 | pre-commit + CI | `.pre-commit-config.yaml` с линтером Python и SQL (ruff / sqlfluff); workflow с проверкой defs и pytest; последний прогон CI на head PR зелёный |
| 10 | dlt + модель | `@dlt_assets` грузят 8 таблиц вместо `dbt seed` (row counts совпадают); ассет модели downstream витрин, в metadata есть метрики (числа, ключи из `settings.yml`) |

`data/hints.yaml` — на каждый непройденный критерий короткая подсказка со ссылкой на раздел задания и на документацию Dagster.

## 6. Эталон `Dagster-HW-MLI-26`

Прежде чем писать с нуля, посмотреть готовые куски в `~/gi/@dataengy/mlinside-hw-olist` (dags, orchestration, dbt, docker-compose) и `~/gi/@dataengy/mlinside-demo-02-dagster` (src, dagster.yaml, tests).

```
Dagster-HW-MLI-26/
  pyproject.toml  uv.lock  Makefile  README.md  .pre-commit-config.yaml
  .github/workflows/ci.yml           # uv sync → dg check defs → pytest → dbt parse
  config/ .env.example .env.local.example
  dbt/olist/                         # dbt-проект из ДЗ 1 (staging, 4+ витрины, тесты)
  src/olist_dagster/
    definitions.py                   # обычный dg.Definitions(...) — явнее для студента, чем load_from_defs_folder
    defs/
      raw/      seeds.py (6–9: dbt seed)  dlt_olist.py (10: @dlt_assets из kagglehub CSV)
      dbt/      assets.py (@dbt_assets + DagsterDbtTranslator: группы, deps на raw)
      ml/       features.py  train.py (sklearn LogisticRegression: опоздание доставки; metrics → metadata)
      automation/ schedules.py (daily)  conditions.py (eager на витринах)  freshness.py
      sensors/  telegram.py (run_failure_sensor → Telegram Bot API через ресурс)
      resources.py                   # DuckDBResource, DbtCliResource, TelegramResource; по DAGSTER_ENV
  tests/  test_assets.py (materialize_to_memory на маленьком CSV)  test_defs.py
  docs/screenshots/                  # lineage, run, freshness, telegram
```

- **Ветки по уровням:** `tier-7`, `tier-9`, `main` (= 10). Проверка `make check` из `MLInside-2026-homeworks/Dagster` должна давать 7, 9 и 10 — это и есть регрессионный набор для чекера.
- **Секреты:** только `.env.local` (в `.gitignore`); в CI — GitHub Secrets.
- **Модель:** таргет `is_late = delivered > estimated` на витрине заказов; time-based split; в metadata — `roc_auc`, `accuracy`, `n_train`, `n_test`.

## 7. Этапы

| Этап | Что сделать | Готово, когда |
|---|---|---|
| 0 ✅ | Уточнить версии `dagster` / `dagster-dbt` / `dagster-dlt` (Context7); вынести путь `settings.yml` в параметр у `doctor.py` и `check_hw.py` в `dbt/` | `dbt/` тесты зелёные |
| 1 ✅ | Эталон уровня 6–7: seeds + dbt-ассеты + checks + schedule + README | `dagster asset materialize --select '*'` зелёный |
| 2 ✅ | `Dagster/` toolchain: Makefile, config, `inspect_defs.py`, критерии 1–6, фикстуры `empty` и `tier7` | `make check` на эталоне `tier-7` → **6** (критерии 1–6; 7 дадут только критерии 7–9 на этапе 4), на `empty` → 0 |
| 3 ✅* | Эталон 8–9: automation, freshness, Telegram, resources по окружениям, pytest, pre-commit, CI | CI зелёный (*локально, на чистой копии; на GitHub — после создания репо, §13) |
| 4 | Критерии 7–9, фикстура `tier9` | на `tier-9` → 9 |
| 5 | Эталон 10: `@dlt_assets`, ML-ассет | метрики в UI |
| 6 | Критерий 10, `MANUAL.md`, `wizard.py`, строка в корневом README («автопроверка») | на `main` → 10 из 10 |

## 8. Проверка самого чекера

- `pytest Dagster/tests`:
  - фикстуры-мини-проекты на 1–2 ассета (без сети, `--no-gh`);
  - юнит-тесты разбора JSON из `inspect_defs`;
  - счёт баллов по `Criterion`.
- Сквозной прогон на трёх ветках эталона (7 / 9 / 10) — вручную перед каждым релизом ДЗ.
- `--json` — стабильный формат, на нём основаны тесты.

## 9. Риски

- **API Dagster меняется** (components / `dg`, `FreshnessPolicy` нового образца, `AutomationCondition`). Интроспекция должна опираться на публичные атрибуты `AssetsDefinition` / `AssetSpec`. Версии закрепить в `requirements.txt` и указать в README.
- **Разные раскладки проектов студентов** (`dg`-проект, модуль, `workspace.yaml`): `wizard.py` спрашивает и пишет `HW_DAGSTER_MODULE`; `inspect_defs` поддерживает все три варианта.
- **Время полной материализации:** `--no-run` для быстрого прогона, таймауты — в `settings.yml`.
- **Нет сети** (kagglehub, GitHub): как в `dbt/` — ошибка в поле `error` критерия, без падения всего прогона.

## 10. Версии (этап 0)

Сверено 2026-10-16: API — по документации Dagster через Context7, номера версий — с PyPI.

| Пакет | Версия | Заметка |
|---|---|---|
| `dagster`, `dagster-webserver` | 1.13.26 | Python 3.10–3.14 |
| `dagster-dbt` | 0.29.26 | жёстко `dagster==1.13.26`; `dbt-core>=1.7,<1.13`; Python **<3.14** — общий потолок для `Dagster/` |
| `dagster-dlt` | 0.29.26 | `dlt` ставится отдельно |
| `dlt` | 1.31.0 | `dlt[duckdb]` |
| `dbt-core` / `dbt-duckdb` | 1.12.6 / 1.11.0 | в `dbt/config/requirements.txt` нижние границы `>=1.8` — для `Dagster/` закрепить `~=` |

Что подтверждено документацией:

- **dbt:** `@dbt_assets(manifest=...)` + `DbtCliResource` (`yield from dbt.cli(["build"], context=context).stream()`). `load_assets_from_dbt_manifest` и `dbt_cli_resource` удалены. dbt-тесты становятся asset checks (singular-тесту нужен `meta.dagster.ref`).
- **dlt:** `@dlt_assets(dlt_source=..., dlt_pipeline=...)` + `DagsterDltResource` (`yield from dlt.run(context=context)`).
- **Автоматизация:** `AutomationCondition.eager()` (можно задавать и на `define_asset_job`); блокирующая проверка — аргумент `blocking` у `@asset_check`.
- **Свежесть:** в документации API есть класс `FreshnessPolicy` (`time_window`, `cron`), в dagster-dbt политика задаётся через `meta.dagster.freshness_policy`. Точные сигнатуры проверить при реализации этапа 1 на установленной 1.13.26 — публичный API здесь менялся.
- **Не проверено:** `dg` / components (`DbtProjectComponent`) — в эталоне этап 1 начинаем с `@dbt_assets`, как самого стабильного варианта.

## 11. Этап 1: итоги

Эталон уровня 6–7 собран и проверен: **21 ассет** (8 raw + 6 staging + 7 marts), **43 asset check — все пройдены**, внешних ассетов нет,
`dagster asset materialize -m olist_dagster.definitions --select '*'` зелёный (`olist_orders_dataset` = 99 441), `pytest` — 8 passed.
Основа — dbt-проект `~/gi/@dataengy/dbt-hw-MLI-26` (без дефолта `olist.duckdb` в `profiles.yml`: правило «env без дефолтов»).

**Где лежит.** Из сессии `~/gi/@dataengy/` недоступен на запись, поэтому заготовка эталона лежит в `.claude/ref/Dagster-HW-MLI-26/`
(каталог `.claude/` в `.gitignore` репозитория ДЗ, в коммиты не попадает). Её надо перенести в `~/gi/@dataengy/Dagster-HW-MLI-26`,
инициализировать репозиторий, первый коммит сделать в ветку `tier-7` и запушить под аккаунтом `dataengy`.

**Что вылезло при реализации (для чекера и ДЗ):**

- dbt не знает рёбер seed → `source()`, поэтому единый `dbt build` ставит staging раньше seeds. Нужны два мультиассета (`dbt seed` и `dbt build --exclude resource_type:seed`).
- Модели читают `source('raw', …)`, а seeds — отдельные ассеты: без подмены зависимости получается разрыв lineage и внешние ассеты. dagster-dbt запрещает seed и source с одним ключом, поэтому подмена идёт в `DagsterDbtTranslator.get_asset_spec`. **Критерий 3 чекера должен ловить именно это** (внешние ассеты вместо seeds в группе raw).
- `from __future__ import annotations` ломает определение `@dbt_assets`: Dagster проверяет аннотацию `context` по реальному классу. `inspect_defs.py` и шаблон для студента это учитывают.
- dbt читает `DBT_PROJECT_DIR` из окружения, а относительный путь считает от каталога проекта; ручной `dbt parse` с относительным `--project-dir` пишет в manifest относительный `root_path`, и seeds не находят CSV. Manifest собирает `make prepare`.
- `DbtProject.preparer.prepare()` запускает `dbt deps` (сеть, `hub.getdbt.com`); в песочнице он частично перезаписал `dbt_packages`. В эталоне `prepare` делает только `dbt parse`, пакеты ставит `make deps`.
- Singular- и unit-тесты dbt asset checks не создают (нужен `meta.dagster.ref`): checks — только generic-тесты из `schema.yml`. Решить на этапе 3: добавить `meta` или оставить как есть.
- `dagster definitions validate` помечен как устаревший в пользу `dg check defs` (нужен `dagster-dg-cli` и `[tool.dg]`) — вернуться к этому в CI на этапе 3.

**Не сделано на этапе 1:** скриншоты lineage и запуска (`docs/screenshots/`, делаются вручную из `make dev`), `make data` не проверен
(нужен Kaggle; в тестах использованы seeds из `dbt-hw-MLI-26`), ветка `tier-7` и push.

**Общий Postgres (`~/.apps/pg`, готовит другая сессия).** На момент этапа 1 каталога ещё нет. Планируется на этапе 3 для `prod`-окружения:
хранилище инстанса Dagster (`dagster.yaml`: `storage.postgres` с `DAGSTER_PG_*` из `config/.env.local`) и dbt-таргет `postgres` (в `profiles.yml`
он уже есть, ключи `PG*` — в `.env.example`). Для уровня 6–7 и для автопроверки остаётся DuckDB. Перед этапом 3 проверить, что Postgres поднят
и какие порт/БД/пользователь выданы.

## 12. Этап 2: итоги

Инструмент `Dagster/` собран: `Makefile` (`setup`, `ready`, `check`, `test`), `config/`, `scripts/{check_hw,inspect_defs}.py`, `scripts/settings.yml`, `data/hints.yaml`, `tests/`.
Полный прогон на эталоне (`.claude/ref/Dagster-HW-MLI-26`, DuckDB во временный файл): **5 из 10 при `--no-gh`** (6 с PR) — критерии 1–5 проходят,
в том числе 8/8 raw-таблиц, 43 asset check зелёные, 6/6 витрин сходятся с `control_figures.json`. На фикстуре `empty` — 0. Тесты: `Dagster/tests` — 15 passed, `dbt/tests` — 42 passed (запускать раздельно).

**Что сделано сверх плана:** общий код вынесен из `dbt/scripts/check_hw.py` в `criteria.py` (модель критериев и отчёт) и `olist_data.py` (сверка raw и витрин с эталоном);
вывод dbt-чекера до и после сверен построчно — идентичен. Критерии 7–10 есть в отчёте как заглушки (статус «info»), чтобы шкала «N из 10» не менялась по мере добавления проверок.

**Решения и ограничения:**

- Всё обращение к Dagster проекта студента — в `inspect_defs.py`, он запускается интерпретатором проекта (`HW_DAGSTER_PYTHON` или `.venv` проекта) и печатает JSON. Сам `check_hw.py` зависит только от `pyyaml` и `duckdb`.
- Чекер добавляет каталог интерпретатора проекта в `PATH` дочерних процессов: без этого `dagster-dbt` не находит `dbt` (в обычной работе это делает активация venv).
- `@definitions` (LazyDefinitions) разворачивается через `load_fn`; вариант с контекстом (`ComponentLoadContext.for_test()`) не проверен на реальном `dg`-проекте.
- Критерий 3 определяет dbt-ассеты по kind `dbt`, staging — по ключу `^stg_`, витрины — остальные dbt-ассеты с upstream. Студенты с другими именами staging получат отказ; регулярка вынесена в `settings.yml` (`graph.staging_regex`).
- Критерий 6 требует в описании PR версию `dagster-dbt` (регэксп `pr_versions`); отдельно `dagster`, `dbt-core` и адаптер не проверяются.
- Реальная проверка GitHub (`pr_report`) для Dagster не прогонялась: репозитория эталона ещё нет, тесты подставляют отчёт синтетически.
- `--no-run` читает данные из DuckDB и `HW_DAGSTER_HOME`, если он задан; без него критерии 4 и 5 по запуску не пройдут.
- Не сделано: `wizard.py` и `MANUAL.md` (этап 6), `make data` (данные студент берёт тем же `fetch_olist_seeds.py` из `dbt/`).

## 13. Этап 3: итоги (эталон 8–9)

Эталон — по-прежнему в staging `.claude/ref/Dagster-HW-MLI-26` (= будущая ветка `tier-9`); снимок уровня 6–7 —
`.claude/ref/Dagster-HW-MLI-26.tier-7` (= ветка `tier-7`). Что сделано (параметры — `config/settings.yml`, секции
`automation`, `retry`, `raw_checks`, `alerts`, `environments`):

| Пункт задания | Как в эталоне | Чем проверено |
|---|---|---|
| Declarative automation | `AutomationCondition.eager()` на staging и витринах (в `OlistTranslator.get_asset_spec`); свой `AutomationConditionSensorDefinition` с `default_status=RUNNING` — встроенный `default_automation_condition_sensor` создаётся выключенным | `test_automation_and_freshness`, `test_sensors_start_running` |
| Freshness | `FreshnessPolicy.time_window(fail=48 ч, warn=26 ч)` на витринах. Демон freshness с 1.12 включён по умолчанию — `freshness: enabled` в `dagster.yaml` **не нужен** (в подготовке было ошибочно) | `test_automation_and_freshness` |
| Retry + блокирующий check | `RetryPolicy` на обоих dbt-мультиассетах; 5 `@asset_check(blocking=True)` на raw: не пусто, ключ уникален | `test_raw_checks_are_blocking`; `test_blocking_check_stops_downstream` (мутация `blocking=False` → тест падает) |
| Ресурсы по окружениям | `environments`: `DAGSTER_ENV` → `notifier` (`log` в dev/test, `telegram` в prod); prod-инстанс — `config/dagster.prod.yaml`, `storage.postgres.postgres_url: {env: DAGSTER_PG_URL}` (URL без пароля, пароль — `~/.pgpass`) | `test_notifier_by_environment`; Postgres — **не проверен** (сервер не поднят) |
| Telegram-алерт | `@run_failure_sensor` (RUNNING) → ресурс `notifier`; `TelegramNotifier` (urllib, `EnvVar` для токена и чата) | `test_failure_sensor_sends_alert` (реальный упавший запуск → `build_run_status_sensor_context(...).for_run_failure()`); реальная отправка — **не проверена** (нет токена) |
| pytest для ассетов | 16 тестов: граф, checks, automation, сенсоры, алерт, блокировка, полная материализация | `make test` — 16 passed |
| pre-commit | `.pre-commit-config.yaml`: pre-commit-hooks (yaml, eof, whitespace, private key) + локальные ruff и sqlfluff через `uv run` (версии из `uv.lock`) | хуки по отдельности на чистой копии; сам `pre-commit run` — **нет** (staging не git-репо) |
| CI | `.github/workflows/ci.yml`: `uv sync --frozen` → seeds-заголовки → `dbt deps` + `prepare` → `pre-commit run --all-files` → `dagster definitions validate` → `pytest -m "not slow"` | имитация на чистой копии (`/tmp/claude-501/ci-sim.sh`) — все шаги зелёные; на GitHub — после создания репо |

Находки, важные для чекера (этап 4):

- **Чистый клон без CSV рвёт граф:** без файлов в `seeds/` dbt не видит seed-узлы, raw-слой становится внешними ассетами,
  а тесты графа падают. В эталоне CI кладёт в seeds только заголовки (`tests/fixtures/seed_headers/`). У студентов
  CI будет падать так же — подсказка в `hints.yaml` для критерия 9.
- **sqlfluff + dbt templater:** templater задаётся только в `.sqlfluff` каталога запуска. Поэтому `.sqlfluff` лежит в
  корне (`project_dir = dbt/olist`). На dbt-проекте из ДЗ 1 было 102 нарушения; стилевые правила AL01, ST07, AM05
  и ST05 исключены, layout исправлен `sqlfluff fix`, два ложных RF02 — `-- noqa: RF02`. В `noqa` после кода правила
  не должно быть текста, иначе sqlfluff его не распознаёт.
- **env до нашего кода:** `dagster dev` читает `dagster.yaml` (а значит, и `DAGSTER_PG_URL`) раньше `load_env()`.
  Решение — `python -m olist_dagster.settings <cmd>`: подгружает `config/.env*`, не перетирая окружение, и делает
  `exec` команды (`make dev-prod`, sqlfluff).
- Чекер на эталоне 8–9 даёт 5/10 с `--no-gh`, как и раньше: регрессии по критериям 1–5 нет.

**Общий Postgres `~/.apps/pg`:** порт **5433**, `localhost`, у проекта своя БД и роль (`just project-add <имя>` в `~/.apps/pg`), пароль — в `~/.pgpass`.
На 2026-10-23 `pg_isready -p 5433` → «no attempt». Нужно `just up` и `just project-add dagster_hw`; это делает пользователь,
потому что команда пишет в `~/.pgpass`. После этого — `make setup-prod && make dev-prod` и скриншот запусков из Postgres.
