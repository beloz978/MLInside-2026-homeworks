CREATE TABLE events (ts DateTime, user_id UInt64, url String, domain String) ENGINE=MergeTree ORDER BY ts;
INSERT INTO events SELECT toDateTime(ts_unix), user_id, url FROM file('/tmp/e.csv','CSVWithNames');
SELECT count() FROM events;
SELECT * FROM events;
