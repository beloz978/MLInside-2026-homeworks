# Plan v2: Dagster + dlt + dbt (PokeAPI -> DuckDB -> dbt models), dg layout

<!-- hardlinks:
- /Users/user/.claude/plans/cheeky-crafting-otter.md
	- backups: /Users/user/.claude/plans/cheeky-crafting-otter.md.bak*
- /Users/user/_/dlt_demo/.ai/plans/cheeky-crafting-otter.md
-->

> **Статус: ЗАМЕНЁН (2026-10-08).** Актуальный план реализации: `~/.claude/plans/kind-booping-codd.md`
> (ревью этого плана и задачи Т0–Т5). Проектная документация: `/Users/user/_/dlt_demo/docs/`
> (`README.md`, `overview.md`, `architecture.md`, `runbook.md`, `sources.md`, `roadmap.md`, `adr/0001–0006`).
> **План реализации dbt-подпроекта (Т2–Т3, шаги Ш0–Ш10 с проверками и рисками):**
> `/Users/user/_/dlt_demo/.ai/plans/2026-10-08-dbt-subproject.md` (ссылка также в `.ai/TODO.md`).
> Ниже исходный план, исправленный по фактам реализации; исправленные места помечены **[факт]**.

## Context

**[факт]** v1 перенесён в dg-раскладку и проверен запуском. Git: `main` = `c7e3a10 1st commit`
(README.md, config/config.yaml, .gitignore, pyproject.toml, .pre-commit-config.yaml), работа идёт в `feat/dagster-dlt-dbt`
(`edb6135`: dg-проект и dlt-подпроект). PyPI доступен, `uv sync` выполнен. Версии: dagster и dagster-dg-cli 1.13.25,
dagster-dlt и dagster-dbt 0.29.25, dlt 1.31.0, dbt-core 1.12.5, dbt-duckdb 1.11.0, duckdb 1.5.6, Python 3.13.
Источники проекта: Colab «dlt pipeline in 4 steps» и курс freeCodeCamp T23Bs75F7ZQ, разбор в `docs/sources.md`.

References (берём только структуру и соглашения):
- Dagster skill: `DbtProjectComponent` (YAML) вместо `@dbt_assets`; dbt `source()` даёт ключ `[source_name, table_name]`.
- `dagster-io/ebook-scaling-data-teams`: раскладка `src/<pkg>/defs/<компонент>/` и dbt-проект в корне.
- `dlt-hub/dlt-dbt-workable`: `sources.yml` над датасетом dlt, `stg_*`, `dim_*`.
- `dlt-hub/dlt-mcp`: MCP для разработки, в runtime не нужен.

## Target layout (/Users/user/_/dlt_demo) — **[факт] исправлено**

```
pyproject.toml            # [tool.dg] + [tool.dg.project] root_module=dlt_demo; dev-группа: dg-cli, webserver, ruff, ty, sqlfluff(+dbt), prek
.env.template  .env       # только DUCKDB_PATH (абсолютный!) и DLT_DATASET_NAME; DLT_PIPELINE_NAME не нужен
.gitignore  .pre-commit-config.yaml   # prek: ruff, ruff-format, ty (+ sqlfluff в Т2, git_hygiene)
.claude/settings.json     # worktree.bgIsolation=none + SessionStart/SessionEnd session-lock hooks
config/config.yaml        # pokemon: {url, pipeline_name, table_name}
src/dlt_demo/definitions.py               # @dg.definitions -> load_from_defs_folder(project_root=…parent.parent.parent)
src/dlt_demo/defs/__init__.py             # нужен, иначе dg scaffold пишет в definitions.py/<имя>
src/dlt_demo/defs/dlt_ingest/{defs.yaml, loads.py}   # было defs/dlt/pokemon.py; имя dlt_ingest, а не dlt (ADR-0004)
src/dlt_demo/defs/dbt/defs.yaml           # DbtProjectComponent, project: '{{ context.project_root }}/dbt' (скаффолд создаёт только этот файл; сам dbt/ пишется руками)
dbt/{dbt_project.yml, profiles.yml}       # было dbt_project/, стало dbt/; готово (Т2), packages.yml — Ш6
.sqlfluff  .sqlfluffignore                # в КОРНЕ репо, не в dbt/: шаблонизатор dbt задаётся только в .sqlfluff каталога запуска (Ш7)
dbt/models/staging/{_sources.yml, stg_pokemon.sql, _stg_models.yml}   # готово; source dlt.pokemon с meta.dagster.asset_key [dlt, pokemon]
dbt/models/marts/{dim_pokemon.sql, _marts_models.yml}                 # готово
notebooks/dlt_dbt_demo.ipynb  .mcp.json   # Т4
docs/                     # документация на русском
```

## Design — **[факт] исправления**

- **Скаффолд dlt.** Класса `dagster_dbt.DltProjectComponent` нет. Правильно: `uv run dg scaffold defs dagster_dlt.DltLoadCollectionComponent dlt_ingest`.
  Флаги `--source/--destination` задаются только парой, `--project-path` у dlt-компонента нет. Шаг «`dg list components`, иначе `@dlt_assets`» не нужен.
- **dlt-ассет.** Вместо подкласса `DagsterDltTranslator` ключ задаётся в YAML: `translation.key: "dlt/{{ resource.name }}"`, получается `dlt/pokemon` (проверено `dg list defs`).
  **`write_disposition="replace"`**: при дефолтном append строки удваивались бы (ADR-0003).
- **`DUCKDB_PATH` обязан быть абсолютным:** dbt запускается с cwd=`dbt/`. Код падает сразу, проверка в `loads.py` (ADR-0002). `python-dotenv` не нужен: `dg` сам читает `.env`.
- **dbt.** `pokemon_id = cast(regexp_extract(url, '/(\d+)/?$', 1) as integer)` (у url хвостовой `/`). Проект лежит в корневом `dbt/`: namespace-пакет `dbt` он не перекрывает, но `.py` туда не класть.
  **[факт]** Скаффолд `DbtProjectComponent` создаёт только `defs.yaml`, каталог `dbt/` пишется руками. Ручной запуск dbt: `cd dbt; set -a; . ../.env; set +a; export DBT_PROFILES_DIR=.; uv run dbt build`.
  Для `dbt_project_evaluator` на DuckDB нужен `dispatch` (`search_order: [dbt_project_evaluator, dbt]`) в `dbt_project.yml`. Детали и риски: `.ai/plans/2026-10-08-dbt-subproject.md`.
- **Notebook.** MCP для ноутбуков не подключается, поэтому `.ipynb` писать через Write/NotebookEdit. DuckDB открывать только с `read_only=True`.
- **Линтинг (добавлено):** ruff, ty, sqlfluff (+templater dbt), dbt_project_evaluator, prek (ADR-0006).
- **Git:** GitHub flow без worktree (ADR-0005). Коммиты идут через временный индекс (`commit-hunks`), потому что параллельно работают несколько сессий.
  Используются advisory-блокировки (`agent-session-lock.sh`) и хуки SessionStart/SessionEnd.
- Вне скоупа (без изменений): schedules, pagination, partitions, деплой в Dagster+.

## Blockers — **[факт] сняты**

1. Сеть: PyPI доступен, `uv sync` прошёл.
2. Git: выполнен `git init -b main`, создан `.claude/settings.json` (`bgIsolation: none`).

## Verification — статус

1. `dg check defs` проходит. `dg list defs` показывает `dlt/pokemon` (группа `pokemon`, kinds dlt, duckdb): **сделано**. dbt-ассеты: Т2/Т3.
2. `dg launch --assets 'dlt/pokemon'` трижды, `RUN_SUCCESS`: **сделано**. `--assets '*'`: Т3.
3. `pokemon_data_1.pokemon` = 20 после повторных запусков: **сделано**. `pokemon_dbt.dim_pokemon` = 20: Т3.
3a. **dbt (Ш2–Ш5 выполнены запуском):** `dbt debug` — All checks passed; `dbt build` — PASS=8 ERROR=0 (2 теста источника, view `stg_pokemon`, table `dim_pokemon`, 4 теста моделей). Не закоммичено.
4. Граф lineage dlt → dbt в `dg dev`: Т3. **Не проверено:** совпадают ли ключ dbt-источника и ассет `dlt/pokemon` (риск — две отдельные вершины); `group_name: pokemon` в `defs/dbt/defs.yaml` ещё не задан.
5. Notebook: Т4. 6. dlt-mcp: Т4.
