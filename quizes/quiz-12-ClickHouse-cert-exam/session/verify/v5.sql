CREATE TABLE ev (day DateTime, user_id UInt64) ENGINE=MergeTree ORDER BY day;
INSERT INTO ev SELECT parseDateTime(day, '%d.%m.%Y'), user_id FROM file('/tmp/d.csv', 'CSVWithNames', 'day String, user_id UInt64');
SELECT * FROM ev ORDER BY day;
SELECT 'bad-toDateTime'; SELECT toDateTime('31.12.2025');
SELECT 'bad-bestEffort'; SELECT parseDateTimeBestEffort('31.12.2025');
SELECT 'bad-cast'; SELECT CAST('31.12.2025' AS DateTime);
-- R3
CREATE TABLE s (cat String, item String, n UInt32) ENGINE=MergeTree ORDER BY cat;
INSERT INTO s VALUES ('a','x',5),('a','y',3),('a','z',9),('b','p',1),('b','q',2);
SELECT cat,item,n FROM s ORDER BY cat, n DESC LIMIT 2 BY cat;
-- R4
CREATE TABLE p (d Date, user_id UInt64, v UInt32, PROJECTION by_user (SELECT user_id, sum(v) GROUP BY user_id)) ENGINE=MergeTree ORDER BY d;
INSERT INTO p SELECT today(), number%100, 1 FROM numbers(100000);
EXPLAIN indexes=1 SELECT user_id, sum(v) FROM p GROUP BY user_id;
-- R5
CREATE TABLE sm (day Date, n UInt64) ENGINE=SummingMergeTree ORDER BY day;
INSERT INTO sm VALUES ('2026-10-01',1);INSERT INTO sm VALUES ('2026-10-01',2);
SELECT 'raw'; SELECT * FROM sm;
SELECT 'agg'; SELECT day,sum(n) FROM sm GROUP BY day;
-- R6
SELECT 'r6-one-arg';
CREATE TABLE rr (id UInt64, updated_at DateTime, is_deleted UInt8) ENGINE=ReplacingMergeTree(is_deleted) ORDER BY id;
SELECT 'r6-two'; CREATE TABLE rr2 (id UInt64, updated_at DateTime, is_deleted UInt8) ENGINE=ReplacingMergeTree(updated_at, is_deleted) ORDER BY id;
INSERT INTO rr2 VALUES (1,'2026-10-01 00:00:00',0),(1,'2026-10-02 00:00:00',1);
SELECT 'final', count() FROM rr2 FINAL;
