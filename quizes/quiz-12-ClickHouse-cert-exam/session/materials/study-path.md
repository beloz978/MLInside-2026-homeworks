# Study path: ClickHouse Certified Developer (4 weeks × 8–10 h)

> Supersedes the week plan in `cert-prep-plan.md` (that file keeps the overview), aligned with the **official objectives** (see `objectives.yaml`). Priorities: H objectives first; course-only topics are light.

| Week | Course modules / labs (learn.clickhouse.com) | Objectives | Hands-on beyond the labs | Checkpoint |
|---|---|---|---|---|
| **1** (9 h) | M1–M2 (Labs 1.1–1.3, 2.1); M4 (Lab 4.1); M6 (Lab 6.1, dictionaries) | D1.1–D1.4 | Smoke test; 3 tables with justified ORDER BY + types; a dictionary + `dictGet` | Mini-mock 1: 3 modeling tasks in 30 min |
| **2** (9 h) | M3 (Labs 3.1–3.2); M5 (Labs 5.1–5.2) | D2.1–D2.4, D3.1–D3.4 | Load UK prices via `url()`, PyPI Parquet via `s3()`, a broken CSV via `FROM INFILE` with transformations; 10 analytic queries (bucketing, quantiles, uniq, substring search) | Mini-mock 2: 4 insert/analyze tasks in 40 min |
| **3** (10 h) | M7 (Labs 7.1–7.2); M8 (Labs 8.1–8.6) | D4.1–D4.4, D5.1–D5.3 | MV (plain + AggregatingMergeTree + SummingMergeTree); projection + set/minmax index proven with `EXPLAIN indexes = 1`; upserts with RMT; update sequences with CMT; the projection + DELETE trap | Mini-mock 3: 4 optimize/dedup tasks in 40 min |
| **4** (9 h) | Review M9–M10 lightly (optional) | all | **2 full mocks** (10–12 tasks, 120 min, docs-only), error log, docs sprints | Mock ≥ 80% twice, then buy the attempt and take it within the week |

## Daily loop (from week 2)
1. 20 min: 2–3 tasks from `clickhouse-cert-dev-guru` (drill mode) on the weakest objective.
2. 10 min: docs sprint (find 5 pages from `doc-bookmarks.md` in ≤ 60 s each).
3. Log every miss in `wiki/error-log.md` (objective, what went wrong, doc link).

## Booking rule
Two timed full mocks ≥ 80% with ≤ 110 min used → buy ($200) and take it the same week (an attempt is valid 365 days; no scheduling needed).
