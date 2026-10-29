# Materials catalog: ClickHouse Certified Developer

> Researched 2026-10-15. Tiers: T1 official · T2 reputable/vendor-adjacent · T3 community · T4 low-signal. Format match = how close it is to the real exam (hands-on SQL in `clickhouse-client`, 10–12 tasks, 2 h). Braindumps are excluded on purpose.

| # | Title | Type | Tier | Date | Fresh | Format | Domains | Cost | Hours | Verdict | URL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Certification page + FAQ (official objectives) | exam guide | T1 | live 2026-10 | Y | n/a | all | free | 0.5 | **MUST**: the source of truth for scope | https://clickhouse.com/learn/certification |
| 2 | Real-time Analytics with ClickHouse (on-demand, ~9 h, 10 modules, **22 labs**) | course + labs | T1 | live 2026-10 | Y | **Y** (labs = hands-on SQL) | all (official: "covers all objectives") | free | 9 + labs ≈ 15 | **MUST**: type every lab yourself | https://learn.clickhouse.com/real-time-analytics-with-clickhouse |
| 3 | Same course, instructor-led (Levels 1–3 virtual; 1–2-day in-person in Oslo, London, Dublin, Krakow, Paris) | live training | T1 | Oct–Nov 2026 | Y | Y | all | free | 8–16 | OPTIONAL: only if you want Q&A with instructors | https://clickhouse.com/learn#live-training |
| 4 | ClickHouse docs: pages mapped in `objectives.yaml` / `doc-bookmarks.md` | reference | T1 | live | Y | Y (allowed in exam) | all | free | ongoing | **MUST**: practise navigating them | https://clickhouse.com/docs |
| 5 | Best-practices pages (primary key, data types, avoid mutations, partitioning) | guide | T1 | live | Y | partial | D1, D5 | free | 2 | **MUST** | https://clickhouse.com/docs/concepts/best-practices/choosing-a-primary-key |
| 6 | "Preparing for the ClickHouse Certified Developer Exam" webinar (Rich Raposa, Pablo Musa; 2026-01-08; 1 h) | webinar | T1 | 2026-01 | Y | partial (environment walkthrough) | logistics | free | 1 | **SHOULD**: watch the recording if available (YouTube video with this title found; check that it is on the ClickHouse channel) | https://clickhouse.com/company/events/202512-amer-clickhouse-certified-developer-exam · https://www.youtube.com/watch?v=bLXCYhf5G8Q |
| 7 | Sample datasets used in the course: UK Property Prices (~30M rows CSV), PyPI 2023 Parquet on S3, Amazon/product reviews, NYC taxi | datasets | T1 | live | Y | **Y** | D2, D3, D4 | free | — | **MUST**: practise loading them | https://clickhouse.com/docs/get-started/sample-datasets/uk-price-paid · https://clickhouse.com/docs/get-started/sample-datasets/amazon-reviews · https://clickhouse.com/docs/get-started/sample-datasets/nyc-taxi |
| 8 | ClickHouse Cloud trial / free credits (the course states 300 credits per month) | environment | T1 | 2026-10 | Y | Y | all | free tier | — | **SHOULD**: the course labs assume Cloud. Local Docker is enough for the exam CLI | https://console.clickhouse.cloud/signUp |
| 9 | `clickhouse-best-practices` agent skill (28 rules) | checklist | T1/T2 | 2026-02 | Y | partial | D1, D2, D4 | free | 1 | **SHOULD**: review rules on schema and MVs; ask Claude to review your lab DDL against them | https://github.com/ClickHouse/agent-skills |
| 10 | Our verified smoke test (`smoke-test.sql`, all 5 areas, 26.11) + `clickhouse-cert-dev-guru` drills | practice | own | 2026-10-15 | Y | **Y** | all | free | ongoing | **MUST**: the main practice loop | `./smoke-test.sql`, `../agents/clickhouse-cert-dev-guru.md` |
| 11 | Tinybird: "ClickHouse certification: exam guide for developers" | article | T3 | 2026-09-02 | Y | n/a | overview | free | 0.3 | OPTIONAL: tips ("work every lab yourself", practise system tables); based on official info, not first-hand; vendor marketing | https://www.tinybird.co/blog/clickhouse-certification |
| 12 | Official announcement blog | article | T1 | 2024 | partial | n/a | overview | free | 0.2 | OPTIONAL: background only; superseded by #1 | https://clickhouse.com/blog/first-official-clickhouse-certification |
| 13 | Udemy "ClickHouse Certified Developer Practice Tests 2026" (278 Qs, 5 tests, independent, 3.8★/2 ratings) | question bank | T4 | 2026-09 | ? | **N** (scenario questions; the real exam is hands-on) | ? | paid | 5 | SKIP: wrong format; use only as extra concept quizzes | https://www.udemy.com/course/clickhouse-certified-developer-practice-questions/ |
| 14 | Other Udemy practice tests / open-exam-prep / YouTube "15 sample questions" | question banks | T4 | 2025–26 | ? | **N** | ? | mixed | — | SKIP: multiple-choice style does not match the exam | https://www.udemy.com/course/practice-tests-for-clickhouse-certified-developer/ · https://open-exam-prep.com/practice/clickhouse-certified |
| 15 | Medium "My ClickHouse Journey" (2026-02) | experience post | T4 | 2026-02 | ? | **contradicts the official format** (describes multiple-choice elimination and replication lag) | — | free | — | SKIP: unreliable; inconsistent with the hands-on exam | https://medium.com/@pprashanthrs/my-clickhouse-journey-medium-blog-post-d17f00b59e58 |
| 16 | Course modules not in the official objectives: JOINs/dictionaries (M6 → keep dictionaries), sharding/replication (M9), compression/TTL (M10) | course | T1 | live | Y | Y | supporting | free | 3 | SHOULD for M6 (dictionaries are official); OPTIONAL for M9–M10 | (in #2) |

## Coverage matrix

| Area | Official docs | Training (course module / lab) | Practice tasks | Lab environment | Gap |
|---|---|---|---|---|---|
| D1 Modeling | ✅ #4, #5 | ✅ M2 L2.1, M4 L4.1, M6 L6.1 | ⚠️ only course labs + smoke test | ✅ | more PK/type-choice tasks, a **dictionary** task with dictGet → exam bank |
| D2 Inserting | ✅ | ✅ M3 L3.1–3.2 | ⚠️ | ✅ (S3 needs network: check on the Mac) | **imperfect CSV / FROM INFILE / transformations on insert** → exam bank |
| D3 Analyzing | ✅ | ✅ M5 L5.1 | ⚠️ | ✅ | time bucketing + quantiles + uniq drills → exam bank |
| D4 Optimizing | ✅ | ✅ M8 L8.1–8.6 | ⚠️ | ✅ | projection + skip index **verification via EXPLAIN / system tables** |
| D5 Dedup & mutations | ✅ | ✅ M7 L7.1–7.2 | ⚠️ | ✅ | the **projection + lightweight DELETE trap**; CollapsingMergeTree update sequences |

**Main gap:** there is no legitimate exam-format practice bank. Close it with our own performance-based tasks (statement + automated check query): ≥ 3 per H objective (19 × 3 ≈ 60 tasks), generated by `clickhouse-cert-dev-guru` into `wiki/exam-bank.md`.

## Top-5 MUST
1. #1 the official objectives (scope).
2. #2 the Academy course with **all 22 labs typed by hand**.
3. #4/#5 docs, practised as an open-book tool (see `doc-bookmarks.md`).
4. #7 datasets: load each in 2–3 ways (s3, url, FROM INFILE).
5. #10 the smoke test + daily guru drills + 2 timed mocks.
