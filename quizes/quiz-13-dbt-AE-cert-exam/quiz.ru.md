---
audience: "Data engineers и аналитики, готовящиеся к dbt Analytics Engineering Certification (dbt Core 1.11)"
purpose: "Полноразмерный пробный экзамен dbt AE: 65 сценарных вопросов на английском с разбором на русском, формат и время как на экзамене"
goal: "Выбирать конфигурацию, команду или тест dbt под задачу — incremental и microbatch, snapshots, contracts и versions, unit и data tests, отладка, source freshness, state и slim CI"
context: "Study guide dbt 1.11, семь доменов (веса dbt Labs не публикует); экзамен: 65 вопросов, 120 минут, проходной балл 65%; проект MyCerts; материалы сессии — в каталоге session/"
prerequisites: "SQL, 6+ месяцев работы с dbt (models, ref/source, tests, incremental)"
duration_min: 120
---

Тест 13. dbt Analytics Engineering Certification (cert exam)

Полноразмерный пробный экзамен в формате dbt Analytics Engineering (study guide dbt 1.11): вопросы на английском, разбор на русском. 65 вопросов: 🟩 знание/понимание — 14, 🟨 применение — 36, 🟥 анализ — 15. Сложность: простой — 12, средний — 38, сложный — 15. Вопросы 6, 12, 23 и 62 — с несколькими ответами (по 1 баллу за каждый верный выбор, штраф за лишний — минус 1, итог не ниже 0), поэтому максимум теста — 69 баллов, а порог 65% — 45 баллов. Домены study guide: D1 Developing and optimizing models — 22 вопроса, D2 Governance — 5, D3 Debugging — 8, D4 Troubleshooting pipelines — 6, D5 Tests — 14, D6 External dependencies — 5, D7 State — 5 (доли оценочные: dbt Labs веса не публикует). Тег домена — в начале «Разбора».

---

Вопрос 1 🟨 применение · средний
Your `fct_orders` model runs on Snowflake and holds about 200 million rows. Each night the source delivers new orders and orders whose status changed; `order_id` is unique. You want each nightly run to process only new and changed rows and to keep exactly one row per order. What should you do?

---

* А) Materialize the model as `table`, so that every run rebuilds it from the full source data
* Б) Use an incremental model with `incremental_strategy='append'` and filter on the last update time
* В) Use an incremental model with `unique_key='order_id'` and filter on the last update time ✅
* Г) Materialize the model as `ephemeral` and let the downstream models select from it

Тема: D1 · Incremental strategies

Разбор: D1. Incremental с `unique_key` на Snowflake по умолчанию использует стратегию `merge`: новые строки вставляются, изменённые обновляются по `order_id`. `append` только добавляет строки и даст дубликаты изменённых заказов. `table` работает, но каждый раз пересчитывает все 200 млн строк, а `ephemeral` вообще не создаёт объект в хранилище (модель встраивается как CTE).

Вопрос 2 🟨 применение · средний
The `stg_vacancies` model parses free-text salary strings with CASE expressions and regex into `salary_min` and `salary_max`. Before merging a change, you want to verify the parsing logic on a few hand-written inputs, including edge cases that do not exist in production data yet. What should you do?

---

* А) Write a singular test that selects rows from the production table where `salary_min > salary_max`
* Б) Add an `accepted_values` test on `salary_currency` in the properties file of the model
* В) Run `dbt source freshness` on the raw vacancies table before every deployment
* Г) Define a `unit_tests` entry with mocked `given` rows and the expected rows in `expect` ✅

Тема: D5 · Unit tests

Разбор: D5. Unit test (dbt 1.8+) описывается в YAML: `model`, `given` (mock-строки для `ref`/`source`) и `expect` (ожидаемый результат). Он проверяет логику SQL на заданных примерах, включая граничные случаи, и запускается `dbt test --select test_type:unit` (в `dbt build` — до сборки модели). Singular и generic data tests проверяют реальные данные уже после сборки, а source freshness проверяет только свежесть загрузки.

Вопрос 3 🟨 применение · простой
You refactored a chain of 30 models and want to quickly confirm that all of them build with the expected columns and types, without reading production data and without paying for full table scans. What should you do?

---

* А) Run `dbt build --empty` ✅
* Б) Run `dbt compile` and read the compiled SQL files of the changed models
* В) Run `dbt run --full-refresh` against a development schema
* Г) Run `dbt parse` and check that the command finishes without errors

Тема: D1 · --empty

Разбор: D1. `--empty` ограничивает `ref()` и `source()` нулём строк (`limit 0`), поэтому модели реально создаются в хранилище со своей схемой, но данные не читаются и стоимость минимальна. `compile` и `parse` в хранилище ничего не создают и не проверяют типы колонок, а `--full-refresh` пересчитает все данные.

Вопрос 4 🟨 применение · средний
A `dbt run` fails with `Database Error in model stg_vacancies: syntax error at or near "AS"`. The compiled SELECT looks fine, so you suspect the statement that dbt wraps around it for the materialization. Which file shows the exact statement that dbt sent to the warehouse, including the `create table ... as` wrapper?

---

* А) `models/staging/stg_vacancies.sql`
* Б) `target/compiled/my_project/models/staging/stg_vacancies.sql`
* В) `target/run/my_project/models/staging/stg_vacancies.sql` ✅
* Г) `target/catalog.json`

Тема: D3 · compiled vs run

Разбор: D3. `target/compiled/` содержит SQL после рендера Jinja (только SELECT), а `target/run/` — полный запрос, отправленный в хранилище: с `create table ... as`, `merge` и т.п. Исходный `.sql` содержит ещё не отрендеренный Jinja, а `catalog.json` — метаданные из `dbt docs generate`, а не SQL. Подробности ошибки есть и в `logs/dbt.log`.

Вопрос 5 🟨 применение · средний
The `dim_employers` model is public and used by several BI dashboards. A recent change renamed one column and changed the type of another, and the dashboards broke. You want dbt to fail the build before the model is materialized whenever its output does not match the agreed columns and data types. What should you do?

---

* А) Add `not_null` and `unique` data tests to every column of the model in its properties file
* Б) Set `contract: {enforced: true}` and declare every column with its `data_type` in YAML ✅
* В) Set `on_schema_change: sync_all_columns` in the config block of the model
* Г) Set `access: public` and assign the model to a `group` in the properties file

Тема: D2 · Model contracts

Разбор: D2. С `contract.enforced: true` dbt сравнивает имена и типы колонок результата с описанием в YAML до создания объекта и падает при расхождении; для каждой колонки нужен `data_type`. Data tests проверяют значения уже после сборки, `on_schema_change` относится к incremental-моделям и меняет схему, а не защищает её, `access` и `group` управляют только тем, кто может делать `ref` на модель.

Вопрос 6 🟥 анализ · сложный
Your `events` source table holds five years of data (about 3 billion rows) with an `event_ts` column. You want dbt to process the data in independent daily batches, so that a failed day can be retried and one month can be reprocessed without touching other months. Which two actions should you take? (Choose two.)

---

* ☑ ✅ Configure `incremental_strategy='microbatch'` with `event_time='event_ts'`, `batch_size='day'`, and `begin`
* ☐ Add an `is_incremental()` filter on `max(event_ts)` inside the model SQL
* ☐ Set `unique_key='event_id'` and use the `delete+insert` strategy
* ☑ ✅ Re-run the model with `--event-time-start` and `--event-time-end` covering that month
* ☐ Run `dbt run --full-refresh --select` for the model

Тема: D1 · Microbatch

Разбор: D1. Microbatch делит модель на независимые батчи по `event_time` (`batch_size`, `begin`); каждый батч — отдельный запрос, и упавший батч можно повторить. Пересчёт месяца делается флагами `--event-time-start` / `--event-time-end`. Фильтр `is_incremental()` в microbatch-модели не нужен (dbt сам ограничивает входы по `event_time`), `delete+insert` с `unique_key` не режет данные на батчи по времени, а `--full-refresh` пересоберёт все пять лет.

Вопрос 7 🟩 понимание · средний
You need one reusable test, `is_positive`, that can be applied to many numeric columns from YAML (for example `salary_min` and `salary_max`). Where should you define it?

---

* А) In `tests/is_positive.sql` as a plain SELECT that returns the failing rows of one table and one column
* Б) In `tests/generic/is_positive.sql` as a `{% test is_positive(model, column_name) %}` block ✅
* В) In `seeds/is_positive.csv` with one row for each column that must be checked
* Г) In `dbt_project.yml` under `vars`, as a SQL string with placeholders for table and column

Тема: D5 · Custom generic tests

Разбор: D5. Custom generic test — это блок `{% test имя(model, column_name) %}` в `tests/generic/` (или в macros); его подключают в `data_tests` любой колонки. SELECT в `tests/` — singular test: он привязан к конкретным таблице и колонке и запускается один раз. Seeds и `vars` тестами не являются.

Вопрос 8 🟥 анализ · сложный
CI builds each pull request into an empty schema. A PR changes only `int_orders`; `stg_orders` (upstream of it) and `fct_orders` (downstream of it) are unchanged. The production `manifest.json` is saved in `./prod-artifacts`. You want CI to build only the changed model and everything downstream of it, and to resolve unchanged upstream models to production. Which command should you run?

---

* А) `dbt build --select state:modified+ --state ./prod-artifacts`
* Б) `dbt build --select state:modified+ --defer --state ./prod-artifacts` ✅
* В) `dbt build --select state:modified --defer --state ./prod-artifacts`
* Г) `dbt build --select +state:modified --defer --state ./prod-artifacts`

Тема: D7 · Slim CI

Разбор: D7. `state:modified+` выбирает изменённые узлы и всех их потомков, `--state` указывает каталог с артефактами prod, а `--defer` подставляет prod-объекты вместо не собранных в CI родителей. Без `--defer` (вариант А) `int_orders` не найдёт `stg_orders` в пустой схеме CI. Без `+` (В) пропадёт `fct_orders`. С `+` слева (Г) соберутся все предки, а потомки не попадут в выборку.

Вопрос 9 🟥 анализ · сложный
A nightly `dbt build` runs with default settings. The `not_null` test (severity `error`) on `stg_orders.order_id` fails. `fct_orders` depends on `stg_orders`; `dim_employers` sits in an unrelated branch of the DAG. What happens next?

---

* А) Nodes downstream of `stg_orders` are skipped, while the unrelated branch keeps building ✅
* Б) dbt stops immediately and rolls back all models that were already built in this run in the warehouse
* В) dbt builds all remaining nodes and reports the failed test only in the final summary
* Г) dbt retries the failed test once and then continues with `fct_orders` if it passes

Тема: D4 · Failure in the DAG

Разбор: D4. В `dbt build` тест — узел DAG: при его ошибке потомки не выполняются и получают статус SKIP, а несвязанные ветки продолжают собираться. Остановка всего запуска происходит только с `--fail-fast`, и даже тогда уже созданные объекты не откатываются. Автоматических повторов нет: упавшее и пропущенное перезапускают через `dbt retry`. Чтобы не блокировать потомков, тесту ставят `severity: warn`.

Вопрос 10 🟨 применение · средний
Your ingestion job loads the table `raw.vacancies` and stamps each row with `_loaded_at`. You want dbt to report a warning when no new rows arrived for 6 hours and an error after 24 hours. What should you do?

---

* А) Add a `not_null` test on `_loaded_at` in the source properties and run `dbt test` every morning
* Б) Add `freshness` settings with the same thresholds to the source properties file, but run only `dbt run`, because it evaluates source freshness automatically after building the models
* В) Run `dbt build --select source:raw`, which checks the freshness of the selected sources
* Г) Set `loaded_at_field` and `freshness` with `warn_after: {count: 6, period: hour}` and `error_after: {count: 24, period: hour}`, then run `dbt source freshness` ✅

Тема: D6 · Source freshness

Разбор: D6. Source freshness задаётся у source (или таблицы): `loaded_at_field` и `freshness` с `warn_after` / `error_after` в виде `{count: N, period: minute|hour|day}`; проверяется отдельной командой `dbt source freshness`, результат пишется в `sources.json`. `not_null` не измеряет возраст данных, а `dbt run` и `dbt build` свежесть источников не проверяют.

Вопрос 11 🟨 применение · средний
In `dbt_project.yml`, the folder `models/marts` sets `+materialized: view`. The properties file for `fct_vacancies` sets `config: {materialized: table}`, and the SQL file of the model starts with `{{ config(materialized='incremental') }}`. How will dbt materialize `fct_vacancies`?

---

* А) As a view, because `dbt_project.yml` sets the default for the whole folder
* Б) As a table, because the properties file overrides the config in the SQL file
* В) As an incremental model, because the `config()` block in the SQL file wins ✅
* Г) dbt raises a compilation error because the same config is set in three places

Тема: D1 · Config precedence

Разбор: D1. Приоритет конфигов: `config()` в `.sql` > `config:` в properties YAML > `dbt_project.yml`. Побеждает самый конкретный уровень, а повторное определение ошибкой не считается.

Вопрос 12 🟨 применение · средний
A data test on `stg_vacancies.employer_id` currently fails the build whenever it finds any bad row. You want it to raise a warning for 1–10 failing rows, to fail the build above 10 rows, and to keep the failing rows in the warehouse for review. Which two actions should you take? (Choose two.)

---

* ☑ ✅ Set `warn_if: ">0"` and `error_if: ">10"` in the config of the test
* ☐ Set `limit: 10` in the config of the test
* ☑ ✅ Set `store_failures: true` in the config of the test
* ☐ Run the build with the `--warn-error` flag
* ☐ Set a `where` clause that keeps only the first 10 rows

Тема: D5 · Test severity and store_failures

Разбор: D5. `warn_if` и `error_if` задают пороги числа упавших строк для предупреждения и ошибки, а `store_failures: true` сохраняет упавшие строки в таблицу (по умолчанию в схему `<target_schema>_dbt_test__audit`). `limit` ограничивает число строк, возвращаемых тестом, но не задаёт порог, `--warn-error` превращает предупреждения в ошибки, а `where` сужает проверяемые строки.

Вопрос 13 🟨 применение · средний
Your CI job must fail whenever dbt emits any warning, for example a deprecation warning, instead of only printing it. What should you do?

---

* А) Add `--fail-fast` to the dbt command in the CI job
* Б) Add `--log-level debug` to the dbt command in the CI job
* В) Add `--no-partial-parse` to the dbt command in the CI job
* Г) Add `--warn-error` to the dbt command in the CI job ✅

Тема: D3 · Flags

Разбор: D3. `--warn-error` превращает предупреждения в ошибки (выборочно — через `--warn-error-options`). `--fail-fast` останавливает запуск на первой ошибке, но предупреждений не касается, `--log-level` меняет только подробность логов, `--no-partial-parse` отключает кеш разбора проекта.

Вопрос 14 🟩 понимание · простой
Which statement about dbt Python models is correct?

---

* А) A `.py` file in `models/` returns a SQL string, which dbt wraps in `create view as` on any adapter that has a Python runtime
* Б) Python models run on the machine that runs dbt and are supported on every adapter, including Postgres
* В) A Python model can be materialized as `view` or `ephemeral` but cannot call `dbt.ref()` for its inputs
* Г) A `.py` file defines `model(dbt, session)` and returns a DataFrame; only `table` and `incremental` are allowed ✅

Тема: D1 · Python models

Разбор: D1. Python-модель — файл `.py` в `models/` с функцией `model(dbt, session)`, которая возвращает DataFrame; внутри доступны `dbt.ref()`, `dbt.source()` и `dbt.config()`. Код выполняется в среде хранилища (Snowpark, Databricks, BigQuery), поэтому поддерживаются не все адаптеры, а материализации — только `table` и `incremental`.

Вопрос 15 🟩 понимание · средний
The `dim_employers` model is defined with versions v1 and v2, and `latest_version: 2` is set in its properties file. A downstream model uses `{{ ref('dim_employers') }}` without a version. Which version does it read?

---

* А) v1, because unversioned references stay on the first version until they are changed by hand
* Б) v2, because an unversioned `ref` resolves to `latest_version` ✅
* В) Both versions, because dbt unions all versions of a model into a single relation
* Г) None; dbt raises an error until the reference specifies `v=` explicitly

Тема: D2 · Model versions

Разбор: D2. Без явной версии `ref` указывает на `latest_version` (если она не задана — на наибольший номер версии). Чтобы остаться на старой версии, пишут `ref('dim_employers', v=1)`, а у v1 задают `deprecation_date`, чтобы потребители увидели предупреждение и мигрировали.

Вопрос 16 🟩 понимание · простой
A model is configured as `ephemeral`. What happens to it when `dbt run` executes?

---

* А) dbt creates a temporary table and drops it at the end of the run in the target schema
* Б) dbt creates no object; the SQL is inlined as a CTE into models that `ref` it ✅
* В) dbt creates a view with the suffix `__dbt_tmp` in the target schema
* Г) dbt skips the model unless it is selected explicitly with `--select`

Тема: D1 · Materializations

Разбор: D1. `ephemeral`-модель не создаёт объект в хранилище: dbt подставляет её SELECT как CTE в модели, которые на неё ссылаются. Поэтому её нельзя запросить напрямую (например, из BI). Временные объекты с суффиксом `__dbt_tmp` (например, `fct_orders__dbt_tmp`) dbt использует внутри других материализаций, а пропуск модели без `--select` не связан с `ephemeral`.

Вопрос 17 🟩 понимание · средний
You need to guarantee that every `employer_id` in `fct_vacancies` exists in `dim_employers`. Which generic test should you define?

---

* А) `unique` on `fct_vacancies.employer_id`
* Б) `relationships` on `dim_employers.employer_id` with `to: ref('fct_vacancies')` and `field: employer_id` in the model properties
* В) `relationships` on `fct_vacancies.employer_id` with `to: ref('dim_employers')` and `field: employer_id` ✅
* Г) `accepted_values` on `fct_vacancies.employer_id` with the full list of employer ids

Тема: D5 · relationships

Разбор: D5. Тест `relationships` вешают на дочернюю колонку, а `to` и `field` указывают на родителя: он ищет значения, которых нет в родительской таблице (orphan keys). Вариант Б проверяет обратное направление: что у каждого работодателя есть вакансия. `unique` проверяет дубликаты, а `accepted_values` с хардкод-списком не масштабируется и не отражает связь таблиц.

Вопрос 18 🟨 применение · простой
You want `dbt build` to stop executing as soon as the first node fails, instead of finishing the independent branches of the DAG. What should you do?

---

* А) Add the `--fail-fast` flag to the command ✅
* Б) Add `--threads 1` so that nodes run one at a time
* В) Add the `--warn-error` flag to the command
* Г) Add `--exclude` with the name of the failing node

Тема: D4 · --fail-fast

Разбор: D4. `--fail-fast` останавливает запуск после первой ошибки. `--threads 1` лишь убирает параллелизм: независимые ветки всё равно будут выполняться. `--warn-error` превращает предупреждения в ошибки, а `--exclude` убирает узлы из выборки заранее.

Вопрос 19 🟥 анализ · сложный
In `dbt_project.yml`, the folder `models/marts` sets `+grants: {select: ['analyst']}`. One model in that folder must be readable by `analyst` and also by `bi_tool`. In the model config you set `grants: {select: ['bi_tool']}`. What is the result?

---

* А) Only `bi_tool` gets `select`, because the model-level list replaces the inherited one ✅
* Б) Both roles get `select`, because dbt always merges grants from all configuration levels
* В) The build fails because the `select` privilege is defined at two different levels
* Г) Only `analyst` gets `select`, because project-level grants cannot be overridden by models

Тема: D1 · Grants

Разбор: D1. По умолчанию грант на модели заменяет унаследованный список для той же привилегии. Чтобы добавить роль к унаследованным, нужен префикс `+`: `grants: {'+select': ['bi_tool']}`. Гранты применяются при сборке модели.

Вопрос 20 🟨 применение · средний
A Looker dashboard, `weekly_vacancies`, reads `fct_vacancies` and `dim_employers`. You want it to appear in the dbt lineage graph and to select the dashboard together with all its upstream models in one command. What should you do?

---

* А) Declare a `source` named `weekly_vacancies` and add `meta` tags to both models
* Б) Add `access: public` to both models and describe the dashboard in their descriptions
* В) Load the dashboard definition with `dbt seed` and reference it with `ref()` in the models, so that dbt tracks the dashboard as a node
* Г) Declare a `dashboard` exposure that depends on both models, then select `+exposure:weekly_vacancies` ✅

Тема: D6 · Exposures

Разбор: D6. Exposure описывает потребителя моделей (dashboard, notebook, analysis, ml, application): `name`, `type`, `owner` и `depends_on`. Он появляется в lineage и docs, а селектор `+exposure:weekly_vacancies` выбирает его вместе со всеми предками (например, в `dbt ls` или `dbt build`). Source описывает входные таблицы, `meta` и `access` на lineage не влияют, а seed — это CSV с данными.

Вопрос 21 🟨 применение · средний
A nightly `dbt build` of 40 nodes failed on node 12 because of a transient warehouse timeout; the remaining nodes were skipped. You want to re-run only the failed and skipped nodes, using the artifacts of the failed run in `target/`, without retyping the selectors. What should you do?

---

* А) Run `dbt build --full-refresh` again with the same selectors
* Б) Run `dbt retry` ✅
* В) Run `dbt build --fail-fast` again with the same selectors
* Г) Run `dbt build --select state:modified+` without any other options

Тема: D7 · dbt retry

Разбор: D7. `dbt retry` читает `run_results.json` последней команды и перезапускает только упавшие и пропущенные узлы с теми же параметрами, пропуская успешные. `--full-refresh` пересоберёт всё, `--fail-fast` лишь останавливает запуск при первой ошибке, а `state:modified+` без `--state` не работает.

Вопрос 22 🟨 применение · средний
To speed up development, you want `dbt run` to build models from only the last 3 days of data. The sources and upstream models define `event_time`. Which command should you run?

---

* А) `dbt run --sample="3 days"` ✅
* Б) `dbt run --empty` with a `limit` of 3 days in every model
* В) `dbt run --select last_3_days`
* Г) `dbt run --vars '{days: 3}'` and a filter in each model

Тема: D1 · --sample

Разбор: D1. `--sample` (dbt 1.10+) ограничивает входные `ref()` и `source()` окном по `event_time`, поэтому у моделей и источников должен быть настроен `event_time`. `--empty` берёт ноль строк, а не последние дни, `--select` выбирает узлы графа, но не строки, а `vars` потребовали бы ручных фильтров в каждой модели.

Вопрос 23 🟩 понимание · средний
Which two built-in generic tests, applied together to one column, make that column a valid primary key? (Choose two.)

---

* ☑ ✅ `unique`
* ☐ `accepted_values`
* ☑ ✅ `not_null`
* ☐ `relationships`
* ☐ `dbt_utils.not_constant`

Тема: D5 · Generic tests

Разбор: D5. Первичный ключ — это уникальные и непустые значения: `unique` + `not_null`. `accepted_values` ограничивает набор значений, `relationships` проверяет ссылочную целостность, а `not_constant` из `dbt_utils` проверяет, что колонка не состоит из одного значения.

Вопрос 24 🟩 понимание · простой
Which command verifies `profiles.yml`, `dbt_project.yml`, and the connection to the warehouse?

---

* А) `dbt debug` ✅
* Б) `dbt parse`
* В) `dbt compile`
* Г) `dbt deps`

Тема: D3 · dbt debug

Разбор: D3. `dbt debug` проверяет версию dbt, наличие и корректность `profiles.yml` и `dbt_project.yml`, зависимости и подключение к хранилищу. `parse` строит граф проекта без подключения к хранилищу; `compile` подключается к нему, но не диагностирует профиль и конфигурацию так, как `debug`; `deps` устанавливает пакеты.

Вопрос 25 🟥 анализ · сложный
On Snowflake, the model `dim_employers` has `contract: {enforced: true}` and a `primary_key` constraint on `employer_id`. A bug loads two rows with the same `employer_id`. What happens?

---

* А) The build fails, because dbt checks that primary key values are unique before it creates the table in the warehouse
* Б) The build fails, because Snowflake enforces primary key constraints at insert time
* В) The build succeeds, because Snowflake does not enforce primary keys; a `unique` data test would catch it ✅
* Г) The build succeeds and dbt removes the duplicate rows automatically after the load

Тема: D2 · Constraints

Разбор: D2. dbt только передаёт ограничение платформе в DDL, а поддержка зависит от хранилища. В Snowflake применяется лишь `not_null`, а `primary_key`, `unique` и `foreign_key` носят информационный характер, поэтому дубликаты не блокируют сборку. Целостность значений проверяют data tests (`unique`, `not_null`), а контракт гарантирует состав и типы колонок.

Вопрос 26 🟨 применение · средний
On BigQuery, the `events_daily` table is partitioned by day. Each run must replace the last three daily partitions completely with freshly computed data, because late events keep changing them. Which configuration fits best?

---

* А) Incremental model with `incremental_strategy='append'` and a filter on the last three days
* Б) Incremental model with `incremental_strategy='insert_overwrite'` and `partition_by` on the event date ✅
* В) Incremental model with `incremental_strategy='merge'` and `unique_key='event_id'` on the whole table in every run
* Г) A `view` that unions the last three days of the source with the previous version of the table

Тема: D1 · insert_overwrite

Разбор: D1. На BigQuery `insert_overwrite` заменяет партиции целиком, не сравнивая строки по ключу, — это подходит, когда последние дни пересчитываются полностью. `append` создаст дубликаты, `merge` сопоставляет строки по `unique_key` и сканирует больше данных, а view не хранит результат.

Вопрос 27 🟨 применение · средний
A one-off business rule joins three models and returns the rows that violate it, for example vacancies that were closed before they were opened. Which type of dbt test fits best?

---

* А) A generic test declared on a single column of `fct_vacancies` with a custom parameter
* Б) A unit test with mocked `given` rows and an `expect` block
* В) A source freshness check on the raw vacancies table
* Г) A singular test: a SQL file in `tests/` that returns the violating rows ✅

Тема: D5 · Singular tests

Разбор: D5. Singular test — это SQL-файл в `tests/`, который возвращает строки, нарушающие правило; тест падает, если строки есть. Он подходит для правил по нескольким моделям. Generic test привязан к колонке и параметризуется, unit test проверяет логику на моках, а freshness измеряет возраст данных.

Вопрос 28 🟨 применение · средний
You want a development schema to contain copies of the production tables so that developers can query them immediately, without rebuilding the models. The production artifacts are in `./prod-artifacts`. Which command should you use?

---

* А) `dbt clone --state ./prod-artifacts` ✅
* Б) `dbt run --defer --state ./prod-artifacts` for all models
* В) `dbt seed --full-refresh` in the development target
* Г) `dbt docs generate --static` with the production target

Тема: D4 · dbt clone

Разбор: D4. `dbt clone` создаёт в целевой схеме копии узлов из состояния, переданного через `--state`: zero-copy clone там, где платформа это поддерживает, иначе view на prod-таблицу. `--defer` лишь подставляет prod-объекты при разрешении `ref` и сам ничего не создаёт, seed грузит CSV, а `docs generate` строит документацию.

Вопрос 29 🟨 применение · средний
You track the history of `dim_employers` with a YAML snapshot. The source has a reliable `updated_at` column and the key `employer_id`. Which configuration is the most efficient way to detect changed rows?

---

* А) `strategy: check` with `check_cols: all` and a `unique_key` on `employer_id`, comparing every column of the row
* Б) `strategy: timestamp` with `unique_key: employer_id` and `updated_at: updated_at` ✅
* В) `strategy: append` with `unique_key: employer_id` and no timestamp column
* Г) `strategy: merge` with `updated_at: updated_at` and no unique key

Тема: D1 · Snapshots

Разбор: D1. Стратегия `timestamp` сравнивает только `updated_at`, поэтому она дешевле, чем `check`, которой нужно сравнивать значения колонок. Для неё задают `unique_key` и `updated_at`, а dbt добавляет колонки `dbt_valid_from` и `dbt_valid_to` (у актуальной версии строки `dbt_valid_to` равен NULL). Стратегий `append` и `merge` у снапшотов нет.

Вопрос 30 🟨 применение · средний
A run fails with: `Compilation Error in model fct_vacancies: depends on a node named 'stg_vacancy' which was not found`. The project contains the model `stg_vacancies`. What is the most likely cause?

---

* А) The warehouse role has no permission to read the table `stg_vacancy`
* Б) The seed behind `stg_vacancy` has not been loaded, so `dbt seed` must run first in the same job
* В) The `ref('stg_vacancy')` call has a typo, or the referenced model does not exist ✅
* Г) The profile target points to a different database than `dbt_project.yml`

Тема: D3 · Compilation errors

Разбор: D3. Эта ошибка возникает на этапе компиляции, ещё до обращения к хранилищу: в проекте нет узла с именем из `ref()`. Нужно исправить имя (`stg_vacancies`) или подключить модель. Права доступа и база в профиле дают Database Error уже при выполнении, а незагруженный seed не влияет на то, найден ли узел в графе.

Вопрос 31 🟨 применение · средний
A `not_null` test on a 2-billion-row table must check only the rows loaded in the last 7 days to keep costs low. What should you configure?

---

* А) `limit: 7` in the config of the test, to read only the last seven days of data
* Б) `severity: warn` in the config of the test
* В) `store_failures: true` in the config of the test
* Г) `where: "loaded_at >= current_date - 7"` in the config of the test ✅

Тема: D5 · Test config: where

Разбор: D5. Параметр `where` добавляет фильтр в запрос теста, поэтому проверяются только нужные строки. `limit` ограничивает число возвращаемых упавших строк, `severity` меняет уровень реакции на падение, а `store_failures` сохраняет упавшие строки — на объём проверки они не влияют.

Вопрос 32 🟩 понимание · средний
What does the selector `state:modified` compare?

---

* А) The results in `run_results.json` of the previous run with the results of the current run, node by node, to find failed nodes
* Б) The current project with the `manifest.json` passed through `--state`, selecting new or changed nodes ✅
* В) The row counts of the tables in the warehouse with the row counts of the previous run
* Г) The files changed in the latest git commit with the files of the target branch

Тема: D7 · state:modified

Разбор: D7. `state:modified` сравнивает текущее описание узлов (код, конфиги, зависимости) с `manifest.json` из каталога `--state` и выбирает новые и изменённые узлы. Статусы выполнения узлов выбираются селектором `result:`, количество строк dbt не сравнивает, а git dbt не читает: сравнение идёт по артефактам.

Вопрос 33 🟨 применение · простой
A clickstream events table is append-only: rows are immutable and never updated. You want the simplest and cheapest incremental model. What should you do?

---

* А) Use `incremental_strategy='delete+insert'` with `unique_key='event_id'`
* Б) Use `incremental_strategy='merge'` with `unique_key='event_id'`
* В) Use `incremental_strategy='append'` without a `unique_key` ✅
* Г) Materialize the model as `table` and rebuild it every night

Тема: D1 · Incremental: append

Разбор: D1. Для неизменяемых событий достаточно `append`: dbt просто вставляет новые строки, не сравнивая их с существующими, поэтому это самая дешёвая стратегия. `merge` и `delete+insert` нужны, когда строки могут обновляться и требуется `unique_key`, а `table` пересчитывает всё при каждом запуске.

Вопрос 34 🟨 применение · средний
The raw table in the warehouse is named `RAW_VACANCIES_V2`, but models should refer to it as `{{ source('hh', 'vacancies') }}`. How do you map the dbt name to the physical table?

---

* А) Set `identifier: RAW_VACANCIES_V2` on the table `vacancies` of the source `hh` ✅
* Б) Set `alias: RAW_VACANCIES_V2` in the config of the source table `vacancies`
* В) Use `{{ ref('RAW_VACANCIES_V2') }}` and keep the source name only in the documentation
* Г) Set `database: RAW_VACANCIES_V2` in the definition of the source `hh`

Тема: D6 · Sources

Разбор: D6. У таблицы источника `name` — это имя для `source()`, а `identifier` — реальное имя таблицы в хранилище. `alias` относится к моделям, `ref()` работает с узлами dbt, а не с сырыми таблицами, `database` задаёт базу, а не таблицу.

Вопрос 35 🟥 анализ · сложный
A model on Postgres has an enforced contract, and the YAML declares `salary_min` as `integer`. After a refactoring, the model SQL returns `salary_min` as `numeric(10,2)` without any cast. What happens when you build the model?

---

* А) dbt casts the column to `integer` silently and logs a warning about the conversion
* Б) dbt builds the model and only warns, because the contract applies to column names
* В) The build fails with a contract error before the object is created; you fix it with a cast in SQL ✅
* Г) dbt creates the table with `numeric(10,2)` and then fails the contract in a post-run step that checks the table

Тема: D2 · Contract enforcement

Разбор: D2. Контракт проверяет и имена, и типы колонок: dbt сверяет результат запроса с YAML до создания объекта и падает с перечнем расхождений. Автоматического приведения типов нет — приведение пишут в SQL (`cast(salary_min as integer)`). Поэтому ни тихий cast, ни предупреждение, ни проверка после создания таблицы не происходят.

Вопрос 36 🟨 применение · средний
You added the column `employer_country` to the SQL of an existing incremental model. You want dbt to add this column to the existing table automatically on the next run, but never to drop existing columns. Which setting fits?

---

* А) `on_schema_change='ignore'`
* Б) `on_schema_change='append_new_columns'` ✅
* В) `on_schema_change='sync_all_columns'` together with a `full_refresh: false` config
* Г) `on_schema_change='fail'`

Тема: D1 · on_schema_change

Разбор: D1. `append_new_columns` добавляет новые колонки и не трогает старые. `ignore` (значение по умолчанию) оставляет таблицу без новой колонки, `sync_all_columns` добавляет новые и удаляет отсутствующие в запросе, а `fail` останавливает запуск с ошибкой.

Вопрос 37 🟥 анализ · сложный
You want a unit test that exercises the `is_incremental()` branch of the incremental model `fct_events`, with rows that already exist in the target table. How do you set that up?

---

* А) Run `dbt test` after the second `dbt run`, because unit tests only work on built tables
* Б) Use a singular test on the built table instead, because unit tests do not support incremental models at all
* В) Add `--full-refresh` to `dbt test` to switch the model into incremental mode
* Г) Set `overrides: macros: is_incremental: true` and pass the existing rows as the `given` input `this` ✅

Тема: D5 · Unit tests for incremental models

Разбор: D5. Для unit-теста инкрементальной ветки переопределяют макрос: `overrides: macros: is_incremental: true`, а строки уже существующей таблицы передают в `given` с `input: this`. Unit-тесты работают на моках входных данных и не требуют собранных upstream-таблиц (но отношение самой тестируемой модели в хранилище должно существовать), поддерживают incremental-модели, а `--full-refresh` наоборот отключает инкрементальную логику.

Вопрос 38 🟨 применение · средний
You want to build `fct_vacancies` together with all of its upstream models, and nothing downstream of it. Which command should you run?

---

* А) `dbt build --select +fct_vacancies` ✅
* Б) `dbt build --select fct_vacancies+`
* В) `dbt build --select @fct_vacancies`
* Г) `dbt build --select fct_vacancies --exclude +fct_vacancies`

Тема: D4 · Graph operators

Разбор: D4. Плюс слева выбирает модель и всех её предков, плюс справа — потомков. `@` выбирает модель, потомков и всех предков этих потомков, а последний вариант исключает саму модель вместе с предками и не оставляет ничего.

Вопрос 39 🟨 применение · средний
`dbt parse` fails with: `mapping values are not allowed in this context` and points to line 12 of `models/staging/_stg.yml`. What should you do first?

---

* А) Check that the warehouse can run the SQL of the models listed in that file, starting from the longest query
* Б) Fix the YAML syntax around line 12, for example the indentation or an unquoted colon ✅
* В) Run `dbt deps` to reinstall the packages used by the models in that file
* Г) Re-run the command with `--full-refresh` so that dbt rebuilds the manifest

Тема: D3 · YAML errors

Разбор: D3. Это ошибка разбора YAML: dbt не смог прочитать properties-файл, поэтому до хранилища дело не доходит. Обычная причина — отступ или двоеточие внутри значения без кавычек. Установка пакетов, `--full-refresh` и проверка SQL на этом этапе не помогут.

Вопрос 40 🟥 анализ · сложный
In the development target the default schema is `dbt_nick`. The model `fct_vacancies` has `+schema: marts` in `dbt_project.yml`, and the project uses the default `generate_schema_name` macro. In which schema does dbt build the model in development?

---

* А) `marts`
* Б) `dbt_nick.marts` as a nested schema inside `dbt_nick`
* В) `prod_marts`
* Г) `dbt_nick_marts` ✅

Тема: D1 · Custom schemas

Разбор: D1. Макрос `generate_schema_name` по умолчанию склеивает схему из target и кастомную: `<target.schema>_<custom_schema>`, то есть `dbt_nick_marts`. В production с `target.schema = prod` получится `prod_marts`. Чтобы использовать кастомную схему без префикса, переопределяют макрос в проекте.

Вопрос 41 🟨 применение · средний
Unit tests use mocked data and are needed only in CI. You want production `dbt build` runs to skip them. What should you do?

---

* А) Add `--exclude test_type:generic` to the production command of the nightly job
* Б) Add `--select test_type:unit` to the production command
* В) Add `--exclude-resource-type unit_test` to the production command ✅
* Г) Add `--no-unit-tests` to the production command

Тема: D5 · Unit tests in production

Разбор: D5. Флаг `--exclude-resource-type unit_test` убирает unit-тесты из выборки, поэтому в production они не запускаются. `test_type:generic` относится к обычным generic data tests, и исключение отключило бы их, а не unit-тесты; `--select test_type:unit` наоборот запустил бы только unit-тесты; флага `--no-unit-tests` в dbt нет.

Вопрос 42 🟨 применение · простой
You want to use macros and tests from the `dbt_utils` package in your project. What should you do?

---

* А) Run `pip install dbt-utils` in the environment where dbt runs
* Б) Add `dbt_utils` to `requirements.txt` and rebuild the virtual environment
* В) Run `dbt seed` to load the package into the project
* Г) Declare the package in `packages.yml` and run `dbt deps` ✅

Тема: D1 · Packages

Разбор: D1. Пакеты dbt объявляют в `packages.yml` (hub, git или локальный путь) и устанавливают командой `dbt deps` в каталог `dbt_packages/`. Это не Python-пакеты, поэтому `pip` и `requirements.txt` не подходят, а `dbt seed` загружает CSV.

Вопрос 43 🟥 анализ · сложный
In your development schema only `fct_orders` has been built; `stg_orders` has not. You run `dbt run --select fct_orders --defer --state ./prod-artifacts`. How is `{{ ref('stg_orders') }}` resolved?

---

* А) The run fails, because `stg_orders` does not exist in the development schema
* Б) It resolves to the production relation of `stg_orders` found in the state manifest ✅
* В) dbt builds `stg_orders` in the development schema first and then builds `fct_orders`
* Г) dbt copies the rows of the production `stg_orders` into a temporary development table

Тема: D7 · --defer

Разбор: D7. С `--defer` dbt для не выбранных и не собранных в текущем target родителей подставляет их relation из `--state` (обычно prod), поэтому `fct_orders` читает prod-версию `stg_orders`. Ничего не копируется и не строится заново. Без `--defer` запуск упал бы с ошибкой отсутствия таблицы.

Вопрос 44 🟩 понимание · простой
After a failed run you need the full log of every statement and error message, including debug-level details. Where does dbt write it by default?

---

* А) `logs/dbt.log` ✅
* Б) `target/run_results.json`
* В) `target/manifest.json`
* Г) `dbt_packages/dbt.log`

Тема: D3 · Logs

Разбор: D3. Полный лог лежит в `logs/dbt.log`. `run_results.json` содержит статусы, время и сообщения по узлам, но не весь лог, `manifest.json` описывает проект и граф, а `dbt_packages/` хранит установленные пакеты.

Вопрос 45 🟨 применение · средний
The source table of vacancies has no reliable `updated_at` column. A new snapshot version must be created whenever `salary` or `title` changes. Which snapshot configuration fits?

---

* А) `strategy: check` with `check_cols: [salary, title]` and a `unique_key` ✅
* Б) `strategy: timestamp` with `updated_at: current_timestamp` and a `unique_key`
* В) `strategy: check` with an empty `check_cols` list and a `unique_key`
* Г) `strategy: timestamp` without `updated_at`, relying on the row order

Тема: D1 · Snapshot: check strategy

Разбор: D1. Стратегия `check` сравнивает значения указанных колонок (`check_cols`) и создаёт новую версию при изменении, поэтому она подходит без `updated_at`. `timestamp` требует настоящую колонку с временем изменения, а `current_timestamp` менялся бы при каждом запуске.

Вопрос 46 🟨 применение · средний
You want to run only data tests (generic and singular) and skip unit tests. Which command should you use?

---

* А) `dbt test --select test_type:generic`
* Б) `dbt test --select test_type:singular`
* В) `dbt test --exclude test_type:data`
* Г) `dbt test --select test_type:data` ✅

Тема: D5 · Test selection

Разбор: D5. `test_type:data` объединяет generic и singular тесты, а unit-тесты имеют тип `unit`. Варианты А и Б запустят только часть data tests, а `--exclude test_type:data` отключит именно то, что нужно запустить.

Вопрос 47 🟥 анализ · сложный
What does `dbt build --select tag:nightly,config.materialized:incremental` select?

---

* А) Nodes that have the tag `nightly` or are incremental models, as a union of both sets of nodes
* Б) Nodes that have the tag `nightly` and are also incremental models, as an intersection ✅
* В) Nodes with the tag `nightly` except those that are materialized as incremental
* Г) Nodes with the tag `nightly` together with their incremental descendants

Тема: D4 · Node selection

Разбор: D4. В синтаксисе выбора запятая без пробелов означает пересечение (AND), а пробел — объединение (OR). Поэтому выбираются только incremental-модели с тегом `nightly`. Исключение делается через `--exclude`, а потомки выбираются оператором `+`.

Вопрос 48 🟨 применение · средний
You want a CI step that checks the freshness of only the `vacancies` table of the source `hh` and fails when the freshness check returns an error. Which command should you use?

---

* А) `dbt test --select source:hh.vacancies`
* Б) `dbt run --select source:hh.vacancies+ --fail-fast`
* В) `dbt source freshness --select source:hh.vacancies` ✅
* Г) `dbt run-operation source_freshness --args '{table: vacancies}'`

Тема: D6 · Freshness command

Разбор: D6. Свежесть проверяет только `dbt source freshness`; выбор источника делается селектором `source:<источник>.<таблица>`, а при статусе error команда завершается с ненулевым кодом, что и нужно CI. `dbt test` запускает тесты источника, а не свежесть, `dbt run` собирает модели и свежесть не проверяет, такого макроса для `run-operation` нет.

Вопрос 49 🟨 применение · средний
A staging model reads `analytics_raw.vacancies` written as a plain table name. The lineage graph shows no upstream node for it, and its freshness cannot be monitored. What should you do?

---

* А) Wrap the table name in `{{ ref('vacancies') }}` and keep the table outside of dbt, without changing the YAML files
* Б) Add `+materialized: view` to the staging model so that dbt registers the table
* В) Load the table with `dbt seed` and read it through a plain table name again
* Г) Declare the table as a source in YAML and read it with `{{ source('raw', 'vacancies') }}` ✅

Тема: D1 · Raw dependencies

Разбор: D1. Сырые таблицы объявляют как source и читают через `source()`: тогда они попадают в DAG и lineage, для них можно настроить freshness и тесты. `ref()` работает с узлами dbt, а не с произвольными таблицами, материализация модели не регистрирует входные таблицы, а seed подходит только для небольших CSV.

Вопрос 50 🟩 понимание · простой
Since dbt 1.8, which key in a properties file holds the generic tests of a column?

---

* А) `unit_tests`
* Б) `checks`
* В) `data_tests` ✅
* Г) `assertions`

Тема: D5 · Test syntax

Разбор: D5. В dbt 1.8+ generic tests на колонке и модели описываются в ключе `data_tests` (старое имя `tests` поддерживается как псевдоним). `unit_tests` — это отдельный верхнеуровневый ключ для unit-тестов, а `checks` и `assertions` в dbt не используются.

Вопрос 51 🟨 применение · средний
Version v1 of `dim_employers` has `deprecation_date: 2026-12-31`. After that date a downstream model still uses `{{ ref('dim_employers', v=1) }}`. What does dbt do?

---

* А) It stops with an error at parse time and refuses to run the project
* Б) It emits a deprecation warning, and the build continues normally ✅
* В) It drops the v1 relation from the warehouse on the deprecation date
* Г) It silently redirects the reference to v2 without any message

Тема: D2 · Deprecation

Разбор: D2. `deprecation_date` — сигнал потребителям: dbt выводит предупреждение при использовании устаревшей версии, но сборка продолжается. Он ничего не удаляет и не перенаправляет `ref`, а ошибкой предупреждение становится только с `--warn-error`.

Вопрос 52 🟨 применение · средний
Which filter inside an incremental model loads only rows newer than those already in the target table?

---

* А) `{% if is_incremental() %} where updated_at > (select max(updated_at) from {{ this }}) {% endif %}` ✅
* Б) `where updated_at > (select max(updated_at) from {{ ref('fct_events') }})` without any condition
* В) `{% if is_incremental() %} where updated_at > current_date {% endif %}` as a fixed daily window
* Г) `{% if not is_incremental() %} where updated_at > (select max(updated_at) from {{ this }}) {% endif %}`

Тема: D1 · is_incremental and this

Разбор: D1. `is_incremental()` истинно, когда таблица уже существует и запуск не `--full-refresh`; тогда фильтр берёт максимум из `{{ this }}` — текущей таблицы. Ссылка модели на себя через `ref` создаёт цикл, фиксированное окно пропустит запоздавшие строки, а инвертированное условие на первом запуске обратится к несуществующей таблице.

Вопрос 53 🟥 анализ · сложный
After switching between two large branches, dbt reports errors about nodes that no longer exist in the project, and you suspect a stale parse cache in `target/partial_parse.msgpack`. Which flag forces dbt to parse the whole project again?

---

* А) `--full-refresh`
* Б) `--fail-fast`
* В) `--no-version-check`
* Г) `--no-partial-parse` ✅

Тема: D3 · Partial parsing

Разбор: D3. dbt кеширует результат разбора проекта (partial parsing) и перечитывает только изменённые файлы. Флаг `--no-partial-parse` отключает кеш и заставляет разобрать проект заново. `--full-refresh` относится к incremental-моделям, `--fail-fast` останавливает запуск на первой ошибке, а `--no-version-check` отключает проверку версии dbt.

Вопрос 54 🟨 применение · средний
The grain of `fct_applications` is the pair (`vacancy_id`, `candidate_id`); each column repeats on its own, but a pair must never repeat. How should you test the grain?

---

* А) Add `unique` tests to both columns separately
* Б) Add `not_null` tests to both columns separately
* В) Add `dbt_utils.unique_combination_of_columns` on the model with both columns ✅
* Г) Add a `relationships` test from each column to its dimension table and a `not_null` test on both

Тема: D5 · Package tests

Разбор: D5. Уникальность пары колонок проверяет тест `unique_combination_of_columns` из пакета `dbt_utils`, который объявляют на уровне модели. Отдельные `unique` на колонках упадут на законных повторах, `not_null` не проверяет уникальность, а `relationships` проверяет ссылки на справочники, но не зерно таблицы.

Вопрос 55 🟩 понимание · простой
You want to see which nodes the selector `tag:nightly+` would run, without running anything. Which command should you use?

---

* А) `dbt compile --select tag:nightly+`
* Б) `dbt ls --select tag:nightly+` ✅
* В) `dbt show --select tag:nightly+`
* Г) `dbt docs generate --select tag:nightly+`

Тема: D4 · dbt ls

Разбор: D4. `dbt ls` (`dbt list`) выводит список узлов, которые выберет селектор, и ничего не выполняет в хранилище. `compile` рендерит SQL, `show` выполняет запрос и показывает строки, а `docs generate` строит документацию.

Вопрос 56 🟥 анализ · сложный
A YAML snapshot (dbt 1.9+) tracks `dim_employers`. When an employer disappears from the source, you want to keep its history and add an extra row that marks the deletion. Which setting fits?

---

* А) `hard_deletes: ignore`
* Б) `hard_deletes: invalidate`
* В) `hard_deletes: new_record` ✅
* Г) `hard_deletes: delete`

Тема: D1 · Snapshot hard deletes

Разбор: D1. `new_record` закрывает версию строки и добавляет новую запись с флагом `dbt_is_deleted`. `ignore` (по умолчанию) удаления не замечает, `invalidate` только проставляет `dbt_valid_to` у последней версии без новой строки, а значения `delete` у настройки нет.

Вопрос 57 🟥 анализ · сложный
The `run_results.json` of last night's failed run was saved to `./last_run`. From another machine, you want to run the models that failed together with all their descendants, using `./last_run` as the state. Which command should you use?

---

* А) `dbt build --select result:error+ --state ./last_run` ✅
* Б) `dbt build --select state:modified+ --state ./last_run`
* В) `dbt build --select result:warn+ --state ./last_run`
* Г) `dbt build --select source_status:fresher+ --state ./last_run`

Тема: D7 · result: selector

Разбор: D7. Селектор `result:<статус>` выбирает узлы по статусу в `run_results.json` из каталога `--state`; `result:error+` — упавшие узлы и их потомки. `state:modified` сравнивает код и конфиги, а не статусы, `result:warn` выбирает предупреждения, а `source_status` работает с результатами `dbt source freshness`.

Вопрос 58 🟨 применение · средний
A `not_null` test is declared on a column of the source table `hh.vacancies`. Which command runs only the tests defined on the source `hh`?

---

* А) `dbt test --select source:hh` ✅
* Б) `dbt source freshness --select source:hh`
* В) `dbt run --select source:hh`
* Г) `dbt build --exclude source:hh`

Тема: D5 · Tests on sources

Разбор: D5. Тесты можно объявлять и на источниках, а запускать их через `dbt test --select source:<имя>`. `dbt source freshness` проверяет возраст данных, а не тесты, `dbt run` выполняет только модели, а `--exclude` убирает узлы, а не выбирает их.

Вопрос 59 🟩 понимание · простой
You want to preview 10 rows of the query behind `stg_vacancies` without materializing anything in the warehouse. Which command should you use?

---

* А) `dbt run --select stg_vacancies --limit 10` in a scratch schema
* Б) `dbt compile --select stg_vacancies`
* В) `dbt docs serve`
* Г) `dbt show --select stg_vacancies --limit 10` ✅

Тема: D1 · dbt show

Разбор: D1. `dbt show` выполняет запрос модели и выводит строки в терминал, ничего не создавая в хранилище; `--limit` ограничивает число строк. `dbt run` материализует модель и флага `--limit` не имеет, `compile` только рендерит SQL, а `docs serve` запускает сайт документации.

Вопрос 60 🟥 анализ · сложный
A pull request fixes `stg_vacancies`, whose `not_null` test was failing. Before merging, you want to verify the fix in your development schema and see whether any downstream model or test breaks. Which command should you run?

---

* А) `dbt build --select stg_vacancies+` ✅
* Б) `dbt run --select stg_vacancies` and nothing else
* В) `dbt parse` and check that it finishes without errors
* Г) `dbt compile --select +stg_vacancies` and read the SQL

Тема: D3 · Verifying a fix

Разбор: D3. `dbt build --select stg_vacancies+` пересобирает модель, запускает её тесты и проверяет потомков, то есть показывает и исправление, и возможные поломки ниже по графу. `run` не запускает тесты, `parse` и `compile` в хранилище ничего не выполняют, поэтому не подтверждают, что данные исправлены.

Вопрос 61 🟨 применение · средний
The same `CASE` expression that normalizes a status column is copied into 12 models, and the column has different names in different models. How do you follow the DRY principle?

---

* А) Move the expression into an `ephemeral` model and join it to every model, then rename the columns in each join
* Б) Store the expression in a seed and read it with `ref()` in each model
* В) Put the expression into a string in `vars` and paste it in each model
* Г) Write a Jinja macro in `macros/` and call it with the column name in each model ✅

Тема: D1 · Macros and DRY

Разбор: D1. Выражение, применяемое к разным колонкам, оформляют макросом Jinja в `macros/` и вызывают `{{ normalize_status('status') }}`. Ephemeral-модель возвращает набор строк, а не выражение, seed хранит данные, а строка в `vars` не параметризуется колонкой и усложняет чтение кода.

Вопрос 62 🟥 анализ · сложный
Which two statements about dbt unit tests are true? (Choose two.)

---

* ☑ ✅ In `given`, you may specify only the columns that the model under test uses
* ☑ ✅ `expect` may list only the columns that you want to compare
* ☐ Unit tests read their input rows from the production tables of the warehouse
* ☐ Unit tests are supported for Python models in the same way as for SQL models
* ☐ In `dbt build`, a unit test runs after the model it tests has been built

Тема: D5 · Unit test details

Разбор: D5. В `given` достаточно колонок, которые использует модель, а в `expect` — тех, что нужно сравнить; остальные можно не указывать. Данные для unit-теста берутся из моков в YAML, а не из таблиц, тесты поддерживаются для SQL-моделей, а `dbt build` запускает unit-тест до сборки модели, чтобы не материализовать модель с неверной логикой.

Вопрос 63 🟩 понимание · средний
Which fields are required to declare an exposure in a properties file?

---

* А) `name`, `url`, and `maturity`
* Б) `name`, `type`, and `owner` ✅
* В) `name`, `type`, and `depends_on`
* Г) `name`, `owner`, and `tags`

Тема: D6 · Exposure fields

Разбор: D6. Обязательные поля exposure — `name`, `type` (dashboard, notebook, analysis, ml, application) и `owner` (имя или email). `depends_on`, `url`, `maturity` и теги необязательны, хотя `depends_on` нужен, чтобы exposure попал в lineage.

Вопрос 64 🟩 понимание · простой
Which layering of models follows dbt project structure best practices?

---

* А) Marts read raw tables, and staging models are built on top of the marts
* Б) One large model per mart reads the sources directly and contains all the logic of the business rules
* В) Staging models join several sources and aggregate them for the business users
* Г) Staging models clean one source each; marts combine them into business entities ✅

Тема: D1 · Modularity

Разбор: D1. Рекомендуемая структура: staging — по одной модели на таблицу источника с лёгкой очисткой (переименование, приведение типов), при необходимости intermediate для сложной логики, и marts — бизнес-сущности и витрины. Так логика не дублируется, а граф остаётся читаемым; остальные варианты нарушают направление зависимостей или смешивают слои.

Вопрос 65 🟨 применение · средний
A mart is read by BI dashboards hundreds of times per day. It joins several tables with about 500 million rows, and its data changes only after the nightly load. How should you materialize it?

---

* А) As a `view`, so that every dashboard query sees the latest source data
* Б) As `ephemeral`, so that the joins are inlined into every dashboard query
* В) As a `table`, rebuilt once after the nightly load ✅
* Г) As a `snapshot`, so that every nightly run keeps a copy of the mart

Тема: D1 · Choosing a materialization

Разбор: D1. Дорогие соединения, частое чтение и редкое обновление — случай для `table` (или incremental, если данных много): расчёт выполняется один раз, а дашборды читают готовый результат. `view` пересчитывал бы соединения при каждом запросе, `ephemeral` вообще не создаёт объект, а `snapshot` нужен для истории изменений источника.

---

Ответы: 1 — В · 2 — Г · 3 — А · 4 — В · 5 — Б · 6 — 1, 4 · 7 — Б · 8 — Б · 9 — А · 10 — Г · 11 — В · 12 — 1, 3 · 13 — Г · 14 — Г · 15 — Б · 16 — Б · 17 — В · 18 — А · 19 — А · 20 — Г · 21 — Б · 22 — А · 23 — 1, 3 · 24 — А · 25 — В · 26 — Б · 27 — Г · 28 — А · 29 — Б · 30 — В · 31 — Г · 32 — Б · 33 — В · 34 — А · 35 — В · 36 — Б · 37 — Г · 38 — А · 39 — Б · 40 — Г · 41 — В · 42 — Г · 43 — Б · 44 — А · 45 — А · 46 — Г · 47 — Б · 48 — В · 49 — Г · 50 — В · 51 — Б · 52 — А · 53 — Г · 54 — В · 55 — Б · 56 — В · 57 — А · 58 — А · 59 — Г · 60 — А · 61 — Г · 62 — 1, 2 · 63 — Б · 64 — Г · 65 — В
