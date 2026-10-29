-- Q1
CREATE TABLE q1 (tenant_id UInt32, ts DateTime, country LowCardinality(String), price Decimal(12,2)) ENGINE=MergeTree ORDER BY (tenant_id, ts);
-- Q2 dictionary
CREATE TABLE countries (id UInt64, name String) ENGINE=MergeTree ORDER BY id;
INSERT INTO countries VALUES (1,'DE'),(2,'FR');
CREATE DICTIONARY dict_country (id UInt64, name String) PRIMARY KEY id SOURCE(CLICKHOUSE(TABLE 'countries')) LAYOUT(FLAT()) LIFETIME(300);
CREATE TABLE orders (order_id UInt64, country_id UInt64) ENGINE=MergeTree ORDER BY order_id;
INSERT INTO orders VALUES (10,1),(11,2);
SELECT order_id, dictGet('dict_country','name',country_id) FROM orders ORDER BY order_id;
SELECT 'wrong-order', dictGet('dict_country', 1, 'name') ; -- expect error
