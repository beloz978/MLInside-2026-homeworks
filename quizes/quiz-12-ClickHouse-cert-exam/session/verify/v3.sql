CREATE TABLE e (ts DateTime, user_id UInt64, v String) ENGINE=MergeTree ORDER BY ts;
INSERT INTO e SELECT toDateTime('2026-10-01 00:00:00')+number, intHash64(number)%100000, 'x' FROM numbers(200000);
ALTER TABLE e ADD INDEX idx_user user_id TYPE set(100) GRANULARITY 4;
SELECT 'no-materialize'; EXPLAIN indexes=1 SELECT count() FROM e WHERE user_id = 42;
ALTER TABLE e MATERIALIZE INDEX idx_user SETTINGS mutations_sync=2;
SELECT 'materialized'; EXPLAIN indexes=1 SELECT count() FROM e WHERE user_id = 42;
SELECT 'modify order by'; ALTER TABLE e MODIFY ORDER BY user_id;
-- Q10
CREATE TABLE p (ts DateTime, user_id UInt64, v String, PROJECTION pr (SELECT user_id, count() GROUP BY user_id)) ENGINE=MergeTree ORDER BY ts;
INSERT INTO p SELECT now()-number, number%10, 'x' FROM numbers(1000);
SELECT 'del1'; DELETE FROM p WHERE user_id=3;
SELECT 'del2-settings-clause'; DELETE FROM p WHERE user_id=3 SETTINGS lightweight_mutation_projection_mode='rebuild';
SELECT 'del3'; ALTER TABLE p MODIFY SETTING lightweight_mutation_projection_mode='rebuild';
DELETE FROM p WHERE user_id=3;
SELECT count() FROM p WHERE user_id=3;
-- Q11
CREATE TABLE r (id UInt64, v String, updated_at DateTime) ENGINE=ReplacingMergeTree(updated_at) ORDER BY id;
INSERT INTO r VALUES (1,'a','2026-10-01 00:00:00');
INSERT INTO r VALUES (1,'b','2026-10-02 00:00:00');
SELECT 'plain'; SELECT * FROM r;
SELECT 'final'; SELECT * FROM r FINAL;
CREATE TABLE r2 (id UInt64, v String, updated_at DateTime) ENGINE=ReplacingMergeTree ORDER BY (id, updated_at);
INSERT INTO r2 VALUES (1,'a','2026-10-01 00:00:00');
INSERT INTO r2 VALUES (1,'b','2026-10-02 00:00:00');
SELECT 'r2 final'; SELECT * FROM r2 FINAL;
-- Q12
CREATE TABLE c (id UInt64, v UInt32, sign Int8) ENGINE=CollapsingMergeTree(sign) ORDER BY id;
INSERT INTO c VALUES (1,10,1);
INSERT INTO c VALUES (1,10,-1),(1,20,1);
SELECT 'cmt final'; SELECT * FROM c FINAL;
CREATE TABLE c2 AS c; INSERT INTO c2 VALUES (1,10,1); INSERT INTO c2 VALUES (1,20,1);
SELECT 'only-new-state'; SELECT * FROM c2 FINAL;
CREATE TABLE c3 AS c; INSERT INTO c3 VALUES (1,10,1); INSERT INTO c3 VALUES (1,20,-1);
SELECT 'wrong-cancel'; SELECT * FROM c3 FINAL;
CREATE TABLE c4 AS c; INSERT INTO c4 VALUES (1,10,1); INSERT INTO c4 VALUES (1,10,1),(1,20,-1);
SELECT 'reversed'; SELECT * FROM c4 FINAL;
