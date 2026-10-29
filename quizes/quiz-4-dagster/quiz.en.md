---
audience: "MLInside 2026 students who have completed the Orchestration module and have done (or are doing) the dbt homework"
purpose: "Check understanding of orchestration in Dagster and get ready for the Dagster homework (self-check and assessment)"
goal: "The student tells assets from tasks and picks the right Dagster mechanism for a typical problem: resources, IO managers, schedules and sensors, partitions, checks, dbt integration, tests"
context: "Quiz after the module «Orchestration: assets, runs, automation, tests»; homework: Dagster/ДЗ/ДЗ_Dagster_Olist.md"
prerequisites: "Quiz 3 (dbt), basic Python and pytest"
duration_min: 20
---

Quiz 4. Orchestrating data and ML pipelines with Dagster

After the module «Orchestration: assets, runs, automation, tests». 10 questions: 🟩 knowledge/understanding — 3, 🟨 application — 5, 🟥 analysis — 2. Difficulty: easy — 3, medium — 5, hard — 2. Questions 1 and 6 have several correct answers (1 point for each correct choice, minus 1 for each extra one, never below 0).

---

Question 1 🟩 understanding · medium
What is true about Dagster and Airflow 3? Select all that apply.

---

* ☑ ✅ In Dagster, a graph node is an asset, i.e. a result (a table, a file, a model)
* ☐ In Airflow 3, runs cannot be scheduled by assets
* ☑ ✅ In Airflow 3, the graph still consists of tasks
* ☐ In Dagster, lineage has to be described by hand
* ☑ ✅ In Airflow 3, an asset is an event that triggers a DAG

Topic: Assets and lineage

Hint: Think about what the node of the graph is in each tool, and what is an event between graphs.

Explanation: Dagster describes not «the work to be done» but the result. Dependencies are set between assets, so lineage builds itself, and checks and metadata are attached to the asset. In Airflow 3 `@asset` simplifies the syntax and lets a DAG run on an event (asset-aware scheduling), but the unit of the graph is still the task.

Question 2 🟩 understanding · easy
Why should an asset take a resource as a parameter (for example `dwh`) instead of creating the connection inside the function?

---

* A) So the asset runs faster thanks to a shared connection
* B) So the connection can change per environment without editing the asset code ✅
* C) So Dagster encrypts the data the asset reads and writes
* D) So every asset runs in a separate process

Topic: Resources

Explanation: the parameter name matches the key in `Definitions(resources={...})`. The asset code does not know whether it is dev or prod; only the resource changes. In a test, a temporary implementation is passed to the same parameter. A resource by itself gives no speed-up, encryption or separate process.

Question 3 🟩 understanding · easy
Who decides where the value returned by an asset is stored, and where the next asset gets it from?

---

* A) IO manager ✅
* B) Asset check
* C) Run storage
* D) Executor

Topic: IO manager

Explanation: the asset only does `return`; saving and loading the value between assets is handled by the IO manager (for example `DuckDBPandasIOManager`, `FilesystemIOManager`). The storage can be changed without touching the asset code. Run storage keeps records of runs, not data; the executor decides how steps are executed (in one process or several); an asset check only validates the result.

Question 4 🟨 application · easy
The schedule is turned on in the UI and the webserver is running, but no runs are created on time. Which component is most likely not running?

---

* A) IO manager
* B) Code server
* C) dagster-daemon ✅
* D) Run launcher

Topic: Schedules and sensors

Explanation: the webserver only shows the state. Schedule and sensor ticks, the run queue and automation are handled by the daemon. Locally `dg dev` starts both the webserver and the daemon, while in production the daemon has to be started separately. Without a code server the UI would show a code location loading error; the run launcher and the IO manager are not separate processes but settings, and they only matter once a run has been created.

Question 5 🟨 application · medium
A sensor watches a folder and creates a run for every new CSV. What guarantees that a repeated tick will not create a second run for the same file?

---

* A) The sensor's `minimum_interval_seconds`
* B) `run_key` in `RunRequest` ✅
* C) The sensor cursor
* D) `partition_key` in `RunRequest`

Topic: Schedules and sensors

Hint: One mechanism answers «where to continue from», the other «do not create what was already created».

Explanation: `run_key` (for example the file name) is an idempotency key: a run with the same `run_key` is not created again. The cursor avoids re-scanning what was already processed, but does not forbid a duplicate by itself; `minimum_interval_seconds` only sets how often the ticks happen, and `partition_key` says which partition to compute.

Question 6 🟨 application · medium
What happens when a dbt project is connected through `dagster-dbt`? Select all that apply.

---

* ☑ ✅ Every dbt model becomes an asset
* ☑ ✅ dbt tests appear as asset checks
* ☐ Running the models' SQL moves from dbt to Dagster
* ☑ ✅ Links between assets are built from `ref` and `source` in `manifest.json`

Topic: dbt integration

Hint: Who actually runs the SQL, and which dbt artifact does Dagster take the project structure from?

Explanation: SQL is still executed by dbt (through `DbtCliResource`, usually `dbt build`), while Dagster reads `manifest.json`, builds assets and lineage from it and shows test results as checks. If the keys of dbt sources do not match the keys of the raw assets, the graph gets a gap: align the keys with `meta.dagster.asset_key` or `DagsterDbtTranslator`.

Question 7 🟨 application · medium
After fixing the logic of an asset with daily partitions, the last 30 days must be recomputed. What should be used?

---

* A) Re-execute the last run from the UI
* B) A backfill over a range of partitions ✅
* C) Wipe the asset's materializations
* D) Reload the code location

Topic: Partitions

Hint: You need to materialize many partitions at once, not repeat a single run.

Explanation: a backfill materializes the selected partitions, and each partition is computed idempotently, so recomputing is safe. Re-execute repeats only the last run, i.e. one partition; wipe only erases the materialization history and recomputes nothing; reload picks up new code but creates no runs.

Question 8 🟥 analysis · hard
Because of a load failure the mart is sometimes empty, yet model training still starts and «successfully» finishes. What fixes the problem best?

---

* A) A RetryPolicy on the training asset with several retries
* B) An asset check `row_count > 0` on the mart with severity WARN
* C) A freshness check on the mart via `build_last_update_freshness_checks`
* D) A blocking asset check on the mart: `row_count > 0` ✅

Topic: Asset checks

Hint: You need a measure that does not merely report the problem but stops dependent assets from running.

Explanation: a retry will repeat the run on the same empty data. A regular check with severity WARN flags the problem but does not stop training. A freshness check watches when the asset was last updated, and the empty mart was updated on time. An asset check with `blocking=True` prevents dependent assets from running in that run when it fails, and with Declarative Automation `all_deps_blocking_checks_passed` does the same. The check result (row_count) also stays in the asset's metadata.

Question 9 🟨 application · medium
How can two related assets be tested in pytest without a database and Docker?

---

* A) Run `dg dev` and run both assets in the UI
* B) Call `dagster asset materialize --select ...` through subprocess
* C) Call `materialize_to_memory` with test resources ✅
* D) Run `dbt test` in a pytest test for the models of these assets

Topic: Testing

Hint: Look for a way to run the assets with Dagster's own machinery, but with replaced resources and no external services.

Explanation: `materialize_to_memory` runs the chain with the real Dagster machinery, passes values between assets itself and plugs in the test resources. CLI materialization and `dg dev` use the real resources and IO manager, i.e. that very database; `dbt test` checks the models' data, not Dagster assets. A single asset can be called as a regular function. In CI, `dg check defs` is additionally run to make sure the definitions load.

Question 10 🟥 analysis · hard
The mart `mart_order_features` lives in the code location `transform`, and `training_dataset` in the code location `ml`. Training must start after the mart is updated. How to organize this?

---

* A) Import the `transform` code into `ml` and call the mart function directly
* B) Merge everything into one code location, otherwise lineage will not be built
* C) Duplicate the mart in `ml` and create a separate asset for it there
* D) Specify `deps=[AssetKey("mart_order_features")]` and run on an event ✅

Topic: Code locations

Hint: Assets from different code locations see each other by key, but do not end up in the same run.

Explanation: assets from different code locations are linked by key without importing code, and in the UI this is a single edge of the graph. But one run does not materialize assets from different locations, so they have to be linked by an event: an automation condition on `training_dataset`, a sensor or a schedule. Separate locations are independent packages and images with a shared graph.

---

Answers: 1 — 1, 3, 5 · 2 — B · 3 — A · 4 — C · 5 — B · 6 — 1, 2, 4 · 7 — B · 8 — D · 9 — C · 10 — D

---

Reserve questions (for a second version of the quiz or a retake)

Reserve 1 🟨 application · medium
Raw loading is sometimes late, and training on the 06:00 schedule runs on yesterday's data. What is the better replacement for the schedule?

---

* A) Move the training schedule an hour later, to 07:00
* B) A `ScheduleDefinition` with a cron every 5 minutes
* C) Add a RetryPolicy to the training and mart assets
* D) Give the training asset the `eager` automation condition ✅

Topic: Automation

Hint: Training should depend on the fact that data was updated, not on the time.

Explanation: the condition lives on the asset and fires when upstream is updated, not by time, so on the day loading is late the training waits instead of running on yesterday's data. A frequent schedule is still tied to time and will retrain the model without new data. Automation conditions are evaluated by the automation sensor inside the daemon, so the daemon is required.

Reserve 2 🟨 application · easy
What should be used to send a Telegram message when a run fails?

---

* A) `@dg.run_failure_sensor` ✅
* B) `@dg.asset_sensor`
* C) `AutomationCondition.eager()`
* D) `AssetCheckSeverity.ERROR`

Topic: Monitoring and alerts

Explanation: `run_failure_sensor` is called when a run fails and receives a context with information about the failure; the message is sent from inside it (for Slack there is a ready `make_slack_on_run_failure_sensor`). `asset_sensor` reacts to an asset materialization, not to a failure; `eager` and severity have nothing to do with notifications. Retries (`RetryPolicy`) and notifications are usually combined: retries first, then the message.

Reserve 3 🟨 application · easy
An asset sometimes fails because an external API is temporarily unavailable. What should be added?

---

* A) A blocking asset check for the external API being unavailable
* B) A `RetryPolicy` with a delay on the asset ✅
* C) A freshness check on the asset with a one-hour tolerance
* D) A second daemon instance for reliability

Topic: Run reliability

Explanation: `RetryPolicy` repeats the failed step (with `delay` and `backoff`), and a temporary failure passes without a manual restart. Asset checks and freshness checks validate the result or its freshness, they do not repeat a step; a second daemon has nothing to do with the external API failing.

Reserve 4 🟩 knowledge · easy
How to show the number of loaded rows next to an asset in the Dagster UI?

---

* A) Set `tags={"row_count": "..."}` in the `@asset` decorator
* B) Print the number with `context.log.info` in the asset body
* C) Create a separate IO manager to store the counter
* D) Return `MaterializeResult` with `metadata={"row_count": n}` ✅

Topic: Metadata

Explanation: materialization metadata is stored with the asset, shown in the UI, and its history is visible across runs (`context.add_output_metadata` does the same). Tags are set when the asset is defined and do not change from run to run; a log stays in the run logs and is not tied to the asset.

Reserve 5 🟥 analysis · hard
After connecting a dbt project, the graph has a raw asset `raw_orders` and a dbt model `stg_orders`, but there is no link between them. What is most likely wrong?

---

* A) The dbt source key does not match the key of `raw_orders` ✅
* B) The `raw_orders` asset has no IO manager configured
* C) The dagster-daemon that updates the graph is not running
* D) The `raw_orders` asset has a different `group_name`

Topic: dbt integration

Hint: dagster-dbt links assets not by table names but by asset keys.

Explanation: dagster-dbt builds links from asset keys; if the key of the dbt source differs from the key of the raw asset, the graph has a gap. Keys are aligned with `meta.dagster.asset_key` in the source description or with `DagsterDbtTranslator`. The daemon does not build the graph, the IO manager is responsible for data, and the group only affects how things are displayed.

Reserve 6 🟩 knowledge · easy
An asset has to be computed per day, starting from 2024-01-01. What should be set in `@asset(partitions_def=...)`?

---

* A) `StaticPartitionsDefinition([...])` with a list of dates
* B) `DailyPartitionsDefinition(start_date="2024-01-01")` ✅
* C) `TimeWindowPartitionMapping(start_offset=-1)`
* D) `ScheduleDefinition(cron_schedule="0 0 * * *")`

Topic: Partitions

Explanation: `DailyPartitionsDefinition` creates a partition for every day from `start_date` by itself. A static list has to be extended by hand; `TimeWindowPartitionMapping` describes how partitions of one asset depend on partitions of another; a schedule launches runs but does not define partitions.

Reserve 7 🟨 application · medium
The DWH resource needs a password. How to pass it so that it is not stored in code and not shown in the Dagster UI?

---

* A) Read `os.getenv("DWH_PASSWORD")` when creating the resource
* B) Pass the password through `run_config` at launch
* C) Set `password=dg.EnvVar("DWH_PASSWORD")` in the resource ✅
* D) Put the password in the resource's `tags` in `Definitions`

Topic: Resources

Hint: The value must be read at run time, and the UI should show only the variable name.

Explanation: `EnvVar` reads the value at run time and the UI shows only the variable name. `os.getenv` reads the value when the code location loads, and it becomes visible in the UI; `run_config` and tags are saved with the run in plain text.

Reserve 8 🟨 application · medium
Assets return a pandas DataFrame. The results must be saved as tables in DuckDB without changing the asset code. What should be plugged in under the `io_manager` key?

---

* A) `DuckDBResource(database="olist.duckdb")`
* B) `FilesystemIOManager(base_dir="data")`
* C) `mem_io_manager` from the standard distribution
* D) `DuckDBPandasIOManager(database="olist.duckdb")` ✅

Topic: IO manager

Hint: You need an IO manager that writes the DataFrame to a table itself, not one that just gives a connection.

Explanation: `DuckDBPandasIOManager` writes the returned DataFrame to a table itself and reads it for the next asset. `DuckDBResource` only gives a connection, and the SQL would have to be written in the asset; `FilesystemIOManager` saves pickle files, and `mem_io_manager` keeps values in the memory of one run.

Reserve 9 🟥 analysis · hard
The mart must be recomputed right after raw is updated, but only if the blocking checks on raw have passed. Which condition should be set on the mart?

---

* A) `AutomationCondition.on_cron("0 6 * * *")`
* B) `AutomationCondition.eager() & AutomationCondition.all_deps_blocking_checks_passed()` ✅
* C) `AutomationCondition.missing() & AutomationCondition.any_deps_updated()`
* D) `AutomationCondition.eager() | AutomationCondition.all_deps_blocking_checks_passed()`

Topic: Automation

Hint: Look at the operator between the conditions: both must hold at once.

Explanation: `eager()` fires on an update of dependencies, and `&` with `all_deps_blocking_checks_passed()` adds the requirement that the upstream blocking checks have passed. With `|` one of the conditions would be enough, and the mart would be recomputed on bad data too. `on_cron` is tied to time, and `missing()` is true only for an asset that has never been materialized.

Reserve 10 🟨 application · easy
`mart_order_features` has to be materialized together with all the assets it depends on. Which asset selection should be used?

---

* A) `AssetSelection.assets("mart_order_features").downstream()`
* B) `AssetSelection.groups("mart_order_features")`
* C) `AssetSelection.assets("mart_order_features").upstream()` ✅
* D) `AssetSelection.assets("mart_order_features")`

Topic: Running and selecting assets

Explanation: `.upstream()` adds everything the asset depends on (in a selection string `+mart_order_features` does the same). `.downstream()` takes the dependent assets, `groups` looks for a group with that name, and a selection without a modifier materializes only the mart itself.

---

Reserve answers: 1 — D · 2 — A · 3 — B · 4 — D · 5 — A · 6 — B · 7 — C · 8 — D · 9 — B · 10 — C
