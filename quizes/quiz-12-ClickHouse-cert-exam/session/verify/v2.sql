CREATE TABLE ev (ts DateTime, user_id UInt64, url String, endpoint String, latency_ms UInt32, tenant_id UInt32) ENGINE=MergeTree ORDER BY (tenant_id, ts);
INSERT INTO ev SELECT toDateTime('2026-10-01 00:00:00')+number*37, number%50, concat('/Checkout/', toString(number%3)), concat('/e', toString(number%4)), (number*7)%500, number%3 FROM numbers(5000);
-- Q5
SELECT endpoint, quantile(0.95)(latency_ms) AS p95, uniq(user_id) AS users FROM ev GROUP BY endpoint ORDER BY p95 DESC LIMIT 10;
SELECT 'q5-wrong'; SELECT quantile(latency_ms, 0.95) FROM ev; -- error expected
SELECT 'q5-percentile'; SELECT percentile(latency_ms, 95) FROM ev; -- error expected
-- Q6
SELECT toStartOfInterval(ts, INTERVAL 15 MINUTE) AS b, count() FROM ev WHERE url ILIKE '%checkout%' GROUP BY b ORDER BY b LIMIT 2;
SELECT 'like-case', count() FROM ev WHERE url LIKE '%checkout%';
SELECT 'ilike', count() FROM ev WHERE url ILIKE '%checkout%';
-- Q7 backfill
CREATE TABLE target (day Date, n UInt64) ENGINE=SummingMergeTree ORDER BY day;
CREATE MATERIALIZED VIEW mv TO target AS SELECT toDate(ts) AS day, count() AS n FROM ev GROUP BY day;
SELECT 'before', count() FROM target;
INSERT INTO ev VALUES (now(), 1, '/a', '/e0', 1, 1);
SELECT 'after-new', sum(n) FROM target;
-- Q8 AMT
CREATE TABLE daily (day Date, users AggregateFunction(uniq, UInt64), revenue SimpleAggregateFunction(sum, UInt64)) ENGINE=AggregatingMergeTree ORDER BY day;
CREATE MATERIALIZED VIEW mv_daily TO daily AS SELECT toDate(ts) AS day, uniqState(user_id) AS users, sum(toUInt64(latency_ms)) AS revenue FROM ev GROUP BY day;
INSERT INTO ev SELECT toDateTime('2026-10-02 00:00:00')+number, number%7, '/x','/e0', 1, 1 FROM numbers(100);
INSERT INTO ev SELECT toDateTime('2026-10-02 00:00:00')+number, number%7, '/x','/e0', 1, 1 FROM numbers(100);
SELECT day, uniqMerge(users) u, sum(revenue) FROM daily WHERE day='2026-10-02' GROUP BY day;
SELECT 'q8 wrong uniq on state:'; SELECT day, uniq(users) FROM daily WHERE day='2026-10-02' GROUP BY day;
-- state with uniq (not State) into AggregateFunction col
SELECT 'q8 A'; CREATE TABLE daily2 AS daily; CREATE MATERIALIZED VIEW mvbad TO daily2 AS SELECT toDate(ts) AS day, uniq(user_id) AS users, sum(toUInt64(latency_ms)) AS revenue FROM ev GROUP BY day;
INSERT INTO ev VALUES (now(), 1, '/a', '/e0', 1, 1);
