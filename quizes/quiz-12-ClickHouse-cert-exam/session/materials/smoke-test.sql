-- ClickHouse cert env smoke test: one statement per exam area. Run: clickhouse-client --multiquery < smoke-test.sql
CREATE DATABASE IF NOT EXISTS prep;
-- 1. Modeling: MergeTree + sensible types + ORDER BY
CREATE OR REPLACE TABLE prep.events (
  ts DateTime, user_id UInt32, event LowCardinality(String), amount Decimal(10,2)
) ENGINE = MergeTree ORDER BY (event, ts);
-- 2. Inserting: generated data with a transformation on insert
INSERT INTO prep.events SELECT now() - number, number % 1000, ['view','click','buy'][number % 3 + 1], (number % 50) / 10 FROM numbers(100000);
-- Dictionary over a table
CREATE OR REPLACE TABLE prep.users (user_id UInt32, country String) ENGINE = MergeTree ORDER BY user_id;
INSERT INTO prep.users SELECT number, ['GE','DE','US'][number % 3 + 1] FROM numbers(1000);
CREATE OR REPLACE DICTIONARY prep.users_dict (user_id UInt32, country String)
  PRIMARY KEY user_id SOURCE(CLICKHOUSE(TABLE 'users' DB 'prep')) LAYOUT(HASHED()) LIFETIME(0);
-- 3. Analyzing: time buckets, uniq, quantiles, dictGet
SELECT toStartOfInterval(ts, INTERVAL 1 HOUR) AS h, dictGet('prep.users_dict', 'country', user_id) AS c,
       count(), uniq(user_id), quantiles(0.5, 0.9)(amount)
FROM prep.events GROUP BY h, c ORDER BY h DESC, c LIMIT 3;
-- 4. Optimizing: aggregating MV, projection, skip index
CREATE OR REPLACE TABLE prep.events_by_hour (h DateTime, event LowCardinality(String), cnt AggregateFunction(count), users AggregateFunction(uniq, UInt32))
  ENGINE = AggregatingMergeTree ORDER BY (event, h);
CREATE MATERIALIZED VIEW IF NOT EXISTS prep.mv_events_by_hour TO prep.events_by_hour AS
  SELECT toStartOfHour(ts) AS h, event, countState() AS cnt, uniqState(user_id) AS users FROM prep.events GROUP BY h, event;
INSERT INTO prep.events SELECT now(), 1, 'buy', 1 FROM numbers(10);
SELECT event, countMerge(cnt), uniqMerge(users) FROM prep.events_by_hour GROUP BY event;
ALTER TABLE prep.events ADD PROJECTION p_user (SELECT * ORDER BY user_id);
ALTER TABLE prep.events MATERIALIZE PROJECTION p_user SETTINGS mutations_sync = 1;
ALTER TABLE prep.events ADD INDEX idx_amount amount TYPE minmax GRANULARITY 4;
ALTER TABLE prep.events MATERIALIZE INDEX idx_amount SETTINGS mutations_sync = 1;
SELECT name, type FROM system.data_skipping_indices WHERE database = 'prep';
SELECT name FROM system.projections WHERE database = 'prep';
-- 5. Dedup & mutations: lightweight delete, ReplacingMergeTree upsert, CollapsingMergeTree update
-- PITFALL: lightweight DELETE on a table with projections throws (code 344) unless this table setting is changed:
ALTER TABLE prep.events MODIFY SETTING lightweight_mutation_projection_mode = 'rebuild';
DELETE FROM prep.events WHERE event = 'view' AND user_id = 0;
CREATE OR REPLACE TABLE prep.users_rmt (user_id UInt32, country String, ver UInt32) ENGINE = ReplacingMergeTree(ver) ORDER BY user_id;
INSERT INTO prep.users_rmt VALUES (1,'GE',1); INSERT INTO prep.users_rmt VALUES (1,'DE',2);
SELECT * FROM prep.users_rmt FINAL;
CREATE OR REPLACE TABLE prep.balance (user_id UInt32, balance Int64, sign Int8) ENGINE = CollapsingMergeTree(sign) ORDER BY user_id;
INSERT INTO prep.balance VALUES (1, 100, 1); INSERT INTO prep.balance VALUES (1, 100, -1), (1, 150, 1);
SELECT user_id, sum(balance * sign) AS balance FROM prep.balance GROUP BY user_id HAVING sum(sign) > 0;
SELECT 'smoke test OK', version();
