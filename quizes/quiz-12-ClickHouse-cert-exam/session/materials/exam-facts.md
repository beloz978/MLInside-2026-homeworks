# ClickHouse Certified Developer: exam facts

> Verified 2026-10-15 against [clickhouse.com/learn/certification](https://clickhouse.com/learn/certification) (page + FAQ). Re-check before buying an attempt.

| Parameter | Value |
|---|---|
| Exam | ClickHouse Certified Developer Exam (the only official ClickHouse certification) |
| Audience | builds or deploys ClickHouse apps: modeling and storage, ingestion, queries, optimization. Prerequisites: none |
| Format | Hands-on, performance-based: **10–12 real-world tasks** on ClickHouse clusters, typed in **`clickhouse-client`** |
| Time | **2 h**; environment setup adds 5–10 min. Breaks allowed, the timer keeps running |
| Passing | **70%**; tasks are **not weighted equally**; topic weights not published |
| Grading | Mostly scripted, **every attempt also reviewed manually**; results by email within 5 business days |
| Price | **$200** per attempt, non-refundable; individual and business purchase links on the page; multiple attempts by email |
| Attempts | Unlimited; **7 days** between attempts; each attempt valid **365 days** from purchase; **no scheduling**, start any time |
| Platform | HackerRank builds the environment and UI; create the HackerRank account with the **same email** as the purchase |
| Language | English only; a **translation site in a separate tab is allowed** |
| Allowed | ClickHouse docs **and other clickhouse.com content (blogs, articles)** in a separate tab; translation tab |
| Forbidden | AI tools (the environment **flags answers that look AI-generated**); external monitors |
| Proctoring | AI-based, no human: webcam identity checks, screen recorded per task, leaving the exam tab monitored (only docs/translation allowed) |
| Validity | Certificate **never expires**; Credly badge + signed certificate + swag |
| Version | ClickHouse version used in the exam: **not published** |
| Contact | certification@clickhouse.com |
| Accommodations | available on request by email |

## Official objectives (5 areas)
1. **Modeling data**: create databases/tables matching criteria or a file format; efficient column types; efficient MergeTree primary key for expected queries; **define and query a Dictionary**.
2. **Inserting data**: insert **local files, cloud-storage files, Parquet/CSV/TSV**; **minor column transformations during insert**; insert from one table into another.
3. **Analyzing data**: queries meeting criteria; regular functions (**substring search, timestamp bucketing**); aggregates (**min, max, sum, avg, unique counts, quantiles**); **GROUP BY time buckets / criteria**.
4. **Optimizing query performance**: **MVs for non-aggregation queries**; **MVs for aggregations with AggregatingMergeTree or SummingMergeTree**; **projections**; **set or minmax skipping indexes**.
5. **Deduplication and mutations**: **lightweight deletes**; **upserts with ReplacingMergeTree**; **frequent updates with CollapsingMergeTree**.

## Diff vs the 2026-10-15 baseline (from the earlier plan)
- **New and important:** the official objectives are now explicit and **narrower** than our baseline list. Skip-index types are named (**set, minmax**); MV targets are named (**AggregatingMergeTree or SummingMergeTree**); **Dictionary** is an explicit modeling objective; **CollapsingMergeTree is for frequent updates**; **lightweight deletes** (not `ALTER DELETE`) are named.
- Not in the official objectives (lower priority, still in the Academy course): JOIN algorithms, window functions, TTL, compression/codecs, sharding/replication, VersionedCollapsingMergeTree, `ALTER UPDATE`, partitions ops, `EXPLAIN`/`query_log` tuning.
- New details: translation tab allowed; other clickhouse.com content (blogs) allowed; AI-looking answers flagged; manual review of every attempt; no scheduling; HackerRank account email must match.
- Recommended training moved to **learn.clickhouse.com** ("Real-time Analytics with ClickHouse", free, about 9 h, 22 labs; covers all objectives).
- Unchanged: format, 2 h, 70%, $200, 7-day retake gap, 365-day attempt validity, no expiry.

## Verified pitfall (on ClickHouse 26.11 local)
`DELETE FROM t …` fails with **Code 344** if `t` has projections, until you run `ALTER TABLE t MODIFY SETTING lightweight_mutation_projection_mode = 'rebuild'` (or `'drop'`). Objectives 4 (projections) and 5 (lightweight deletes) can meet in one task.
