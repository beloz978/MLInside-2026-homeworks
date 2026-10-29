# Doc bookmarks: ClickHouse Certified Developer

> The docs and other clickhouse.com pages are allowed in a separate tab during the exam. Open the HTML version (drop the `.md`) in the browser, and keep this list in a bookmarks folder `CH-EXAM`. All links checked 2026-10-15 (HTTP 200).
> Speed rule: if you don't find the syntax within 60 s, write the simplest working version first and come back later.

**Docs search tips:** search by the exact clause (`ADD PROJECTION`, `TYPE set`, `FROM INFILE`, `lightweight_mutation_projection_mode`), by the function name (`toStartOfInterval`, `quantiles`) or by the engine (`CollapsingMergeTree`). The "Copy page" and "View as Markdown" buttons give clean examples.

## D1. Modeling data

| Obj | Pri | Page | Look up there | Search terms |
|---|---|---|---|---|
| D1.1 | H | [CREATE TABLE](https://clickhouse.com/docs/reference/statements/create/table) | Create databases and tables that meet given criteria or match a file format | CREATE TABLE ... AS / EMPTY AS SELECT, DESCRIBE file(), schema inference, DEFAULT/MATERIALIZED/ALIAS columns |
| D1.1 |  | [MergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/mergetree) | ↳ same objective |  |
| D1.1 |  | [Automatic schema inference from input data](https://clickhouse.com/docs/concepts/features/interfaces/schema-inference) | ↳ same objective |  |
| D1.2 | H | [Selecting data types](https://clickhouse.com/docs/concepts/best-practices/select-data-type) | Choose efficient column data types | LowCardinality, avoid Nullable, smallest UInt/Int, Date vs DateTime, Decimal, Enum, toTypeName, min/max of column |
| D1.2 |  | [LowCardinality(T)](https://clickhouse.com/docs/reference/data-types/lowcardinality) | ↳ same objective |  |
| D1.2 |  | [Nullable(T)](https://clickhouse.com/docs/reference/data-types/nullable) | ↳ same objective |  |
| D1.2 |  | [DateTime64](https://clickhouse.com/docs/reference/data-types/datetime64) | ↳ same objective |  |
| D1.3 | H | [Choosing a primary key](https://clickhouse.com/docs/concepts/best-practices/choosing-a-primary-key) | Define an efficient primary key for a MergeTree table based on expected queries | ORDER BY vs PRIMARY KEY, low cardinality first, filter columns, granules 8192, EXPLAIN indexes = 1 |
| D1.3 |  | [A practical introduction to primary indexes in ClickHouse](https://clickhouse.com/docs/guides/clickhouse/data-modelling/sparse-primary-indexes) | ↳ same objective |  |
| D1.3 |  | [Primary indexes](https://clickhouse.com/docs/concepts/core-concepts/primary-indexes) | ↳ same objective |  |
| D1.4 | H | [CREATE DICTIONARY](https://clickhouse.com/docs/reference/statements/create/dictionary) | Define and query a Dictionary | CREATE DICTIONARY, SOURCE(CLICKHOUSE(TABLE ...)), LAYOUT(HASHED/FLAT/RANGE_HASHED), LIFETIME, dictGet, dictGetOrDefault, JOIN with dictionary |
| D1.4 |  | [ClickHouse dictionary source](https://clickhouse.com/docs/reference/statements/create/dictionary/sources/clickhouse) | ↳ same objective |  |
| D1.4 |  | [Dictionary layouts](https://clickhouse.com/docs/reference/statements/create/dictionary/layouts/overview) | ↳ same objective |  |
| D1.4 |  | [Functions for Working with Dictionaries](https://clickhouse.com/docs/reference/functions/regular-functions/ext-dict-functions) | ↳ same objective |  |
| D1.4 |  | [Dictionary](https://clickhouse.com/docs/concepts/features/dictionaries/index) | ↳ same objective |  |
| D1.5 | L | [Choosing a partitioning key](https://clickhouse.com/docs/concepts/best-practices/partitioning-keys) | Partitioning, TTL, compression codecs (course-only) |  |
| D1.5 |  | [CODEC](https://clickhouse.com/docs/reference/statements/create/table/codec) | ↳ same objective |  |
| D1.5 |  | [ALTER TABLE ... MODIFY TTL](https://clickhouse.com/docs/reference/statements/alter/ttl) | ↳ same objective |  |

## D2. Inserting data

| Obj | Pri | Page | Look up there | Search terms |
|---|---|---|---|---|
| D2.1 | H | [INSERT INTO](https://clickhouse.com/docs/reference/statements/insert-into) | Insert data from local files and files in cloud storage | INSERT INTO t FROM INFILE 'x.csv' FORMAT CSV, clickhouse-client --query ... < file, s3('https://...', 'Parquet'), s3Cluster, url() |
| D2.1 |  | [s3](https://clickhouse.com/docs/reference/functions/table-functions/s3) | ↳ same objective |  |
| D2.1 |  | [url](https://clickhouse.com/docs/reference/functions/table-functions/url) | ↳ same objective |  |
| D2.1 |  | [file](https://clickhouse.com/docs/reference/functions/table-functions/file) | ↳ same objective |  |
| D2.1 |  | [Insert data into ClickHouse Cloud using clickhouse-client](https://clickhouse.com/docs/get-started/quickstarts/insert-data-using-clickhouse-client) | ↳ same objective |  |
| D2.2 | H | [Working with Parquet in ClickHouse](https://clickhouse.com/docs/guides/clickhouse/data-formats/parquet) | Insert Parquet, CSV and TSV files | CSVWithNames, TabSeparatedWithNames, input_format_csv_*, format_csv_delimiter, input_format_allow_errors_num/ratio, skip header |
| D2.2 |  | [Working with CSV and TSV data in ClickHouse](https://clickhouse.com/docs/guides/clickhouse/data-formats/csv-tsv) | ↳ same objective |  |
| D2.3 | H | [INSERT INTO](https://clickhouse.com/docs/reference/statements/insert-into) | Apply minor column transformations during insertion | INSERT INTO t SELECT f(col) FROM s3(...), input() function, parseDateTimeBestEffort, toDecimal, splitByChar, nullIf, column list |
| D2.3 |  | [input](https://clickhouse.com/docs/reference/functions/table-functions/input) | ↳ same objective |  |
| D2.4 | H | [INSERT INTO](https://clickhouse.com/docs/reference/statements/insert-into) | Insert data from one table into another | INSERT INTO t2 SELECT ... FROM t1, column order/names, settings for big copies |
| D2.5 | L | [Asynchronous inserts (async_insert)](https://clickhouse.com/docs/concepts/features/operations/insert/asyncinserts) | Async inserts, batching, ClickPipes (course-only) |  |

## D3. Analyzing data

| Obj | Pri | Page | Look up there | Search terms |
|---|---|---|---|---|
| D3.1 | H | [GROUP BY](https://clickhouse.com/docs/reference/statements/select/group-by) | Write queries that meet given criteria | WHERE/HAVING, ORDER BY ... LIMIT n BY, WITH, subqueries, IN, JOIN basics |
| D3.1 |  | [JOIN](https://clickhouse.com/docs/reference/statements/select/join) | ↳ same objective |  |
| D3.1 |  | [index](https://clickhouse.com/docs/reference/functions/window-functions/index) | ↳ same objective |  |
| D3.2 | H | [Functions for Searching in Strings](https://clickhouse.com/docs/reference/functions/regular-functions/string-search-functions) | Use regular functions, e.g. substring search and timestamp bucketing | position, like/ilike, match, multiSearchAny, hasToken, toStartOfInterval, toStartOfHour/Day/Week/Month, dateDiff, formatDateTime |
| D3.2 |  | [Functions for Working with Dates and Times](https://clickhouse.com/docs/reference/functions/regular-functions/date-time-functions) | ↳ same objective |  |
| D3.3 | H | [Aggregate Functions](https://clickhouse.com/docs/reference/functions/aggregate-functions/reference-index) | Use aggregate functions such as min, max, sum, avg, unique counts and quantiles | uniq vs uniqExact, quantile(0.9)(x), quantiles(0.5,0.9), countIf/sumIf, argMax, topK |
| D3.3 |  | [uniq](https://clickhouse.com/docs/reference/functions/aggregate-functions/uniq) | ↳ same objective |  |
| D3.3 |  | [uniqExact](https://clickhouse.com/docs/reference/functions/aggregate-functions/uniqExact) | ↳ same objective |  |
| D3.3 |  | [quantile](https://clickhouse.com/docs/reference/functions/aggregate-functions/quantile) | ↳ same objective |  |
| D3.3 |  | [quantiles Functions](https://clickhouse.com/docs/reference/functions/aggregate-functions/quantiles) | ↳ same objective |  |
| D3.3 |  | [Aggregate Function Combinators](https://clickhouse.com/docs/reference/functions/aggregate-functions/combinators) | ↳ same objective |  |
| D3.4 | H | [GROUP BY](https://clickhouse.com/docs/reference/statements/select/group-by) | Use GROUP BY to bucket aggregated results by timeframe or other criteria | GROUP BY toStartOfInterval(ts, INTERVAL 15 MINUTE), WITH ROLLUP/CUBE/TOTALS, ORDER BY ... WITH FILL |
| D3.4 |  | [Functions for Working with Dates and Times](https://clickhouse.com/docs/reference/functions/regular-functions/date-time-functions) | ↳ same objective |  |
| D3.5 | L | [Using JOINs in ClickHouse](https://clickhouse.com/docs/concepts/features/operations/select/joining-tables) | JOIN algorithms, window functions, UDFs (course-only) |  |

## D4. Optimizing query performance

| Obj | Pri | Page | Look up there | Search terms |
|---|---|---|---|---|
| D4.1 | H | [Incremental materialized view](https://clickhouse.com/docs/concepts/features/materialized-views/incremental-materialized-view) | Define materialized views for non-aggregation queries | CREATE MATERIALIZED VIEW mv TO target AS SELECT, POPULATE vs backfill INSERT ... SELECT, MV re-sorts data with a different ORDER BY, refreshable REFRESH EVERY |
| D4.1 |  | [CREATE VIEW](https://clickhouse.com/docs/reference/statements/create/view) | ↳ same objective |  |
| D4.1 |  | [Refreshable materialized view](https://clickhouse.com/docs/concepts/features/materialized-views/refreshable-materialized-view) | ↳ same objective |  |
| D4.2 | H | [AggregatingMergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/aggregatingmergetree) | Define materialized views for aggregations using AggregatingMergeTree or SummingMergeTree | AggregateFunction(uniq, T), SimpleAggregateFunction, -State on insert, -Merge on read, sum() again on SummingMergeTree reads |
| D4.2 |  | [SummingMergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/summingmergetree) | ↳ same objective |  |
| D4.2 |  | [Aggregate Function Combinators](https://clickhouse.com/docs/reference/functions/aggregate-functions/combinators) | ↳ same objective |  |
| D4.3 | H | [Projections](https://clickhouse.com/docs/concepts/features/projections/projections) | Define projections on tables | ALTER TABLE ADD PROJECTION p (SELECT ... ORDER BY ...), MATERIALIZE PROJECTION, aggregating projections, system.projections, lightweight_mutation_projection_mode |
| D4.3 |  | [ALTER TABLE ... PROJECTION](https://clickhouse.com/docs/reference/statements/alter/projection) | ↳ same objective |  |
| D4.3 |  | [Create your first projection](https://clickhouse.com/docs/get-started/quickstarts/create-your-first-projection) | ↳ same objective |  |
| D4.3 |  | [Materialized views versus projections](https://clickhouse.com/docs/concepts/features/projections/materialized-views-versus-projections) | ↳ same objective |  |
| D4.4 | H | [Understanding ClickHouse data skipping indexes](https://clickhouse.com/docs/concepts/features/performance/skip-indexes/skipping-indexes) | Define set or minmax skipping indexes | INDEX idx col TYPE minmax GRANULARITY n, TYPE set(100), ALTER TABLE ADD INDEX + MATERIALIZE INDEX, system.data_skipping_indices, EXPLAIN indexes = 1 |
| D4.4 |  | [Data skipping index examples](https://clickhouse.com/docs/concepts/features/performance/skip-indexes/skipping-indexes-examples) | ↳ same objective |  |
| D4.5 | M | [EXPLAIN](https://clickhouse.com/docs/reference/statements/explain) | EXPLAIN, query_log, PREWHERE (supporting skills) |  |
| D4.5 |  | [query_log](https://clickhouse.com/docs/reference/system-tables/query_log) | ↳ same objective |  |
| D4.5 |  | [How does the PREWHERE optimization work?](https://clickhouse.com/docs/concepts/features/performance/prewhere) | ↳ same objective |  |

## D5. Deduplication and mutations

| Obj | Pri | Page | Look up there | Search terms |
|---|---|---|---|---|
| D5.1 | H | [Lightweight delete](https://clickhouse.com/docs/concepts/features/operations/delete/lightweight-delete) | Perform lightweight deletes | DELETE FROM t WHERE ..., _row_exists, projections need lightweight_mutation_projection_mode, vs ALTER TABLE DELETE |
| D5.1 |  | [DELETE](https://clickhouse.com/docs/reference/statements/delete) | ↳ same objective |  |
| D5.2 | H | [ReplacingMergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/replacingmergetree) | Implement efficient upserts with ReplacingMergeTree | ReplacingMergeTree(ver[, is_deleted]), ORDER BY = dedup key, SELECT ... FINAL, OPTIMIZE ... FINAL (avoid in prod), argMax pattern |
| D5.2 |  | [Working with the ReplacingMergeTree engine](https://clickhouse.com/docs/concepts/features/operations/update/replacing-merge-tree) | ↳ same objective |  |
| D5.3 | H | [CollapsingMergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/collapsingmergetree) | Implement efficient frequent updates with CollapsingMergeTree | CollapsingMergeTree(sign), cancel row (sign = -1) + new state (sign = 1), sum(x * sign) ... HAVING sum(sign) > 0, FINAL |
| D5.3 |  | [VersionedCollapsingMergeTree table engine](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/versionedcollapsingmergetree) | ↳ same objective |  |
| D5.4 | M | [ALTER TABLE ... UPDATE](https://clickhouse.com/docs/reference/statements/alter/update) | Mutations and insert deduplication (supporting) |  |
| D5.4 |  | [ALTER TABLE ... DELETE](https://clickhouse.com/docs/reference/statements/alter/delete) | ↳ same objective |  |
| D5.4 |  | [mutations](https://clickhouse.com/docs/reference/system-tables/mutations) | ↳ same objective |  |
| D5.4 |  | [Avoid mutations](https://clickhouse.com/docs/concepts/best-practices/avoid-mutations) | ↳ same objective |  |
| D5.4 |  | [Deduplication strategies](https://clickhouse.com/docs/concepts/features/operations/insert/deduplication) | ↳ same objective |  |

## Must-memorize (no time to look up)

- `ENGINE = MergeTree ORDER BY (low_card, ..., time)`, `PARTITION BY toYYYYMM(ts)` (only if needed)
- `INSERT INTO t FROM INFILE 'f.csv.gz' COMPRESSION 'gzip' FORMAT CSVWithNames` (clickhouse-client)
- `INSERT INTO t SELECT ... FROM s3('https://.../*.parquet', 'Parquet')`
- `CREATE DICTIONARY d (...) PRIMARY KEY k SOURCE(CLICKHOUSE(TABLE 't')) LAYOUT(HASHED()) LIFETIME(0)` → `dictGet('d','attr',key)`
- `CREATE MATERIALIZED VIEW mv TO target AS SELECT ...` + backfill `INSERT INTO target SELECT ...`
- AggregatingMergeTree: `uniqState()` on insert, `uniqMerge()` on read; SummingMergeTree: still `sum()` on read
- `ALTER TABLE t ADD PROJECTION p (SELECT ... ORDER BY x)` → `ALTER TABLE t MATERIALIZE PROJECTION p`
- `ALTER TABLE t ADD INDEX i col TYPE set(100) GRANULARITY 4` → `MATERIALIZE INDEX i`
- `DELETE FROM t WHERE ...` (if projections exist: `MODIFY SETTING lightweight_mutation_projection_mode = 'rebuild'`)
- `ReplacingMergeTree(ver)` + `SELECT ... FINAL`; `CollapsingMergeTree(sign)` + `sum(x*sign) ... HAVING sum(sign) > 0`
