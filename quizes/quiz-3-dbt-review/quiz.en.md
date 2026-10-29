---
audience: "MLInside 2026 students who have completed the Transformation module (SQL, data warehouse basics)"
purpose: "Check understanding of dbt and get ready for the dbt homework (self-check and assessment)"
goal: "The student understands the role of dbt in ELT and picks the materialization, test and modeling technique for a task: ref/source, incremental models, data tests, macros, snapshots"
context: "Quiz after the module «Transformation: models, tests, materializations»; homework: dbt/ДЗ/ДЗ_dbt_Olist.md"
prerequisites: "SQL, data warehouse basics (ClickHouse, DuckDB)"
duration_min: 20
---

Quiz 3. Data transformation and marts with dbt

After the module «Transformation: models, tests, materializations». 10 questions: 🟩 knowledge/understanding — 3, 🟨 application — 4, 🟥 analysis — 3. Difficulty: easy — 3, medium — 4, hard — 3. Question 5 has several correct answers (1 point for each correct choice, minus 1 for each extra one, never below 0).

---

Question 1 🟩 knowledge · easy
Which part of ETL/ELT does dbt implement?

* A) Extract
* B) Transform ✅
* C) Load
* D) Extract + Load

Topic: The role of dbt in ELT

Explanation: dbt works inside the warehouse, on data that is already loaded: it turns raw tables into models and marts with SQL queries, and it cannot extract or load data — separate tools are needed for that (Airbyte, dlt, your own scripts).

Question 2 🟩 understanding · easy
What does a dbt model file usually contain, and what does dbt do with it?

* A) A trained ML model that dbt runs on new data and saves the predictions to a table
* B) A schedule description by which dbt runs the project build and restarts failed tasks
* C) A SELECT query (SQL with Jinja) that dbt compiles and turns into a view or table in the warehouse ✅
* D) A loading script that dbt executes to copy data from an external source into the warehouse

Topic: Models

Explanation: a model is a SELECT in a `.sql` file; dbt compiles the Jinja, adds `CREATE ... AS` and runs it in the target database. dbt cannot train models, schedule runs or load data — other tools are needed for that. (Python models exist but are not supported by every adapter.)

Question 3 🟩 understanding · easy
What are `ref` and `source` used for in models?

* A) To set a schedule
* B) To choose the materialization (view, table)
* C) To store artifacts
* D) To describe dependencies between models and sources ✅

Topic: ref and source

Explanation: `ref('stg_orders')` refers to another model, `source('olist', 'orders')` to a raw table declared in YAML. From these references dbt builds the DAG and the build order, and also substitutes the schema and object name depending on the target (dev, prod).

Question 4 🟨 application · hard
The orders table in ClickHouse has tens of millions of rows, and new and changed orders with an `updated_at` field arrive every day. The model is materialized as `incremental`. Which strategy should be chosen so there are no duplicate orders and the whole table is not rebuilt?

* A) `delete+insert` with `unique_key='order_id'` and a filter on `updated_at` inside `is_incremental()`: changed orders are deleted and inserted again ✅
* B) `append` with a filter on `updated_at`: new and changed rows are appended, and old versions of orders stay next to the new ones
* C) `legacy` (the default strategy) with `unique_key='order_id'`: dbt updates only the changed orders and touches nothing else in the table
* D) `insert_overwrite` with `unique_key='order_id'`: dbt overwrites the rows with matching keys without touching the other orders

Topic: Materializations

Hint: MergeTree has no cheap row UPDATE: how else can changed orders be replaced without duplicates?

Explanation: MergeTree has no cheap row UPDATE, so changes are applied by deleting and re-inserting. `delete+insert` (needs lightweight delete, ClickHouse 22.8+) collects the changed rows into a temporary table, deletes the orders with those `unique_key` values and inserts them again. `append` only appends, so changed orders are duplicated. On each run `legacy` copies the whole table into a temporary one and swaps it in — in cost this is almost a full rebuild. `insert_overwrite` does not support `unique_key` and replaces whole partitions. Another option is the `ReplacingMergeTree` engine, but then duplicates are removed at read time (`FINAL`). After the model logic changes, rebuild it with `--full-refresh`.

Question 5 🟨 application · medium
Which checks are built-in generic tests? Select all that apply.

* ☑ ✅ `unique`
* ☐ A SQL file in the `tests/` folder that returns rows with violations
* ☑ ✅ `accepted_values`
* ☐ A `unit_tests:` block with `given` and `expect`
* ☑ ✅ `relationships`

Topic: Data tests

Hint: Built-in generic tests are attached to a column in YAML; the other options are other kinds of tests.

Explanation: the built-in generic tests are `not_null`, `unique`, `accepted_values`, `relationships`; they are attached to a column in YAML. A SQL file in `tests/` is a singular test, and a block with inputs and an expected result is a unit test (dbt 1.8+).

Question 6 🟨 application · medium
The segmentation of the order amount (`low` / `mid` / `high`) has to be used in several models. Why move it into an `amount_bucket` macro?

* A) So dbt performs the segmentation faster than a plain `CASE`, because the macro is compiled once and then cached
* B) So the logic lives in one place and is reused across models, and the differences between SQL dialects are hidden inside the macro ✅
* C) So the segmentation result is saved in the warehouse as a separate table and not recomputed in each model
* D) So no tests are needed for this logic, because dbt checks macros automatically on every project build

Topic: Macros

Hint: A macro is Jinja that substitutes SQL at compile time. What does that give you besides speed?

Explanation: a macro is a Jinja function that substitutes SQL into the model at compile time; nothing gets faster because of it. Changing thresholds is done in one place, and the dialect differences (DuckDB, Postgres, ClickHouse) can be hidden inside the macro. Tests are still needed: for the macro's logic you write a unit test of the model.

Question 7 🟨 application · medium
How does a unit test differ from a singular test?

* A) In essence they do not: both check data already loaded into the warehouse, and differ only in where the file is stored, in the name and in how it is run in CI
* B) A unit test is written in Python and run separately from dbt, while a singular test is a SQL query executed by `dbt test` together with the other checks of the project
* C) A unit test checks the project's YAML configuration (column types, descriptions and tests) for correctness, while a singular test checks values in warehouse tables
* D) A unit test checks the model logic against the expected result (`expect`) on given input data (`given`), while a singular test checks the real data in the warehouse ✅

Topic: Data tests

Hint: Compare the data each test works on: data given in YAML or real data in the warehouse.

Explanation: a unit test (dbt 1.8+) feeds fixed rows into the model and compares the result with the expected one, so it catches logic errors before the data arrives. A singular test is arbitrary SQL that returns rows with violations on the real data. Unit tests are written in YAML, not in Python.

Question 8 🟥 analysis · hard
The `unique` test on `stg_orders` fails. The mart `mart_orders` is built from `stg_orders`. What will `dbt build` do with the mart?

* A) Build it as usual: the `unique` test only records duplicates in the results and does not affect the build order
* B) Build it, but mark the rows with duplicates in a service column so they can be filtered out later
* C) Skip the mart (skipped) together with the other dependent resources, because a test on the upstream model failed ✅
* D) Roll `stg_orders` back to the previous version and build the mart on it so the pipeline does not stop

Topic: Data tests

Hint: `dbt build` walks the DAG and runs a model's tests right after the model.

Explanation: `dbt build` walks the DAG and runs models together with their tests; if an upstream resource fails (including a test with severity `error`), all dependent resources are skipped and the command exits with code 1. If you run `dbt run` and then `dbt test`, the mart will already be built on duplicates. dbt has no rollbacks: `stg_orders` stays built, the pipeline just does not go further.

Question 9 🟥 analysis · hard
An order's status changes (`processing` → `shipped` → `delivered`), and analysts need to know the status an order had on any past date. What should be used?

* A) A `snapshot` with the `timestamp` strategy on `updated_at`: dbt closes the old version of the row and adds a new one with validity dates ✅
* B) `incremental` with `unique_key=order_id`: on each run the order row is updated, and past statuses are kept in a service table
* C) A `view` over the orders table: every query reads the data again, so the status history can be obtained for past dates
* D) An `ephemeral` model with a window function over `order_id`: the status history is computed on the fly from the current orders table

Topic: Snapshots

Hint: You need a history of row versions with validity dates (SCD2).

Explanation: a snapshot stores row versions (SCD2): when `updated_at` changes it closes the old version (`dbt_valid_to`) and adds a new one (`dbt_valid_from`). Incremental with `unique_key` overwrites the row, and the history is lost. A snapshot sees only what the source contains at the time of the run, so it has to be run regularly: changes between runs are not saved.

Question 10 🟥 analysis · medium
Raw data is loaded at 05:00 by cron, `dbt build` runs at 06:00 on another machine. One day loading finished at 07:00, and the marts were recomputed on yesterday's data. What is missing?

* A) More generic tests: `not_null` and `accepted_values` on the marts will catch yesterday's data and stop the recomputation
* B) An orchestrator that knows dbt must run after the load, and handles retries and alerts ✅
* C) A switch from Core to another adapter that waits for the source load to finish before building
* D) Moving the models from `marts` to `staging` so they are recomputed earlier and do not depend on the load time

Topic: Data freshness and orchestration

Hint: dbt Core knows nothing about external tasks and has no scheduler of its own.

Explanation: dbt Core is responsible for dependencies between models, but not for the order relative to external tasks (loading), and it has no scheduler. That role is taken by an orchestrator (cron is the minimum, Dagster or Airflow the full answer): running after an event, retries, alerts.

---

Answers: 1 — B · 2 — C · 3 — D · 4 — A · 5 — 1, 3, 5 · 6 — B · 7 — D · 8 — C · 9 — A · 10 — B

---

Reserve questions (for a second version of the quiz or a retake)

Reserve 1 🟩 knowledge · easy
What usually happens in the staging layer?

* A) The final marts are built
* B) Only source data is stored
* C) Fields are renamed, types are cast, and the model stays 1:1 with the source ✅
* D) Aggregates by customer and period are computed

Topic: Model layers

Explanation: staging is a thin layer over the source: renaming, type casting, simple cleaning, no joins or aggregations. Business logic and marts are built above, in intermediate and marts.

Reserve 2 🟨 application · easy
Which materialization does not create an object in the database but is substituted into dependent models as a CTE?

* A) `ephemeral` ✅
* B) `view`
* C) `table`
* D) `incremental`

Topic: Materializations

Explanation: an ephemeral model is embedded into the query of the dependent model, so it cannot be inspected in the database or queried directly. It suits small intermediate steps; view and table create objects, incremental appends data to an existing table.

Reserve 3 🟨 application · medium
On the mart `fct_order_items` the grain is the pair `order_id` + `order_item_id`; neither field is unique on its own. How to test the uniqueness of the grain?

* A) `unique` on `order_id`
* B) `not_null` on both fields
* C) `relationships` between these fields
* D) `dbt_utils.unique_combination_of_columns` with both columns ✅

Topic: Data tests

Hint: Look for a test from the dbt_utils package that checks a combination of columns.

Explanation: `unique` checks one column, and for a composite key the `dbt_utils` package provides a test for the uniqueness of a combination. An alternative is a surrogate key via `dbt_utils.generate_surrogate_key` and a regular `unique` on it.

Reserve 4 🟨 application · easy
What does the `dbt_project_evaluator` package check?

* A) The execution speed of models in production
* B) How well the project follows best practices: DAG structure, naming, test and documentation coverage ✅
* C) The correctness of data in tables
* D) The compatibility of packages with the adapter version

Topic: Project quality

Explanation: the package analyzes the project itself (from the `manifest` metadata) and shows violations: a model without a test or description, a mart that refers to a source directly, wrong prefixes. It does not check the data in tables — for that use generic, singular and unit tests or `dbt_expectations`.

Reserve 5 🟥 analysis · hard
A macro uses a function that exists in DuckDB but fails on Postgres and ClickHouse. How to make the project work on all targets?

* A) Create a separate copy of the project for each database
* B) Rewrite all models in Python
* C) Implement the macro through `adapter.dispatch` (or branching on `target.type`) so the models do not change ✅
* D) Remove the macro and copy the SQL into every model

Topic: Macros

Hint: dbt can choose the macro implementation for a specific adapter.

Explanation: `adapter.dispatch` picks the macro implementation for the adapter (`duckdb__…`, `postgres__…`, `clickhouse__…`, fallback `default__…`), and the models call the same macro. Project copies and duplicated SQL break at the first edit.

---

Reserve answers: 1 — C · 2 — A · 3 — D · 4 — B · 5 — C
