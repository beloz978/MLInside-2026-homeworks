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
    definitions.py                   # load_from_defs_folder / Definitions.merge
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
| 1 | Эталон уровня 6–7: seeds + dbt-ассеты + checks + schedule + README | `dagster asset materialize --select '*'` зелёный |
| 2 | `Dagster/` toolchain: Makefile, config, `inspect_defs.py`, критерии 1–6, фикстуры `empty` и `tier7` | `make check` на эталоне `tier-7` → 7, на `empty` → 0 |
| 3 | Эталон 8–9: automation, freshness, Telegram, resources по окружениям, pytest, pre-commit, CI | CI зелёный |
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
