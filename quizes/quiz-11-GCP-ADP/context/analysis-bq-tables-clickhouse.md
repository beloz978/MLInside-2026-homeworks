# External / BigLake / native таблицы, безопасность колонок и ClickHouse (сжато)

## Типы таблиц
| | External | BigLake (Lakehouse) | Native partitioned |
|---|---|---|---|
| Данные | GCS, Drive, Bigtable | GCS, S3, Azure | хранилище BigQuery |
| Доступ к файлам | у пользователя | у service account connection | — |
| Column/row security, masking | нет | да | да |
| Партиции / кластеризация | hive-партиции / нет | hive + metadata cache | да / да |
| DML, time travel | нет | нет (кроме Iceberg) | да |
| Оплата запросов | Parquet/ORC — прочитанные колонки; Avro/CSV/JSON — все | то же + refresh кеша | прочитанные колонки и партиции |

## Column-level security
Taxonomy + policy tags (Data Catalog / Dataplex) → тег на колонку → enforce access control → роль Fine-Grained Reader. Dynamic data masking: data policy (SHA-256, nullify, default, email, first/last four, date year, custom routine) + роль Masked Reader. Рядом: row access policies, authorized views/datasets, IAM, Analytics Hub, CMEK. Только native, BigLake, Omni — не обычные external.

## Оценка 100M строк × 50 колонок (≈169 GB логически), on-demand $6.25/TiB
Q_A — агрегат 3 колонок за 90 дней из 730; Q_B — JSON-путь по всей таблице; месяц = 5000 Q_A + 200 Q_B.
| Вариант | Q_A | Q_B | $/мес запросы |
|---|---|---|---|
| Native, партиции + кластеры | 0.5–1.5 с | 2–5 с | ≈ $29 |
| BigLake + cache, Parquet/ORC, hive | 1–3 с | 4–10 с | ≈ $29 |
| External Parquet/ORC, hive | 2–6 с | 6–15 с | ≈ $29 (без hive ≈ $99) |
| External/BigLake Avro | 5–20 с | 20–60 с | ≈ $780 (без партиций ≈ $5 000) |
Оценки порядка величин, не бенчмарк; проверять через INFORMATION_SCHEMA.JOBS.

## ClickHouse поверх данных BigQuery
Движка «таблица BigQuery» в ClickHouse нет; MV над внешними данными — только refreshable MV (`REFRESH EVERY …`).
| # | Подход | Q_A | ≈ $/мес |
|---|---|---|---|
| O0 | Только BigQuery (+MV, BI Engine) | 0.3–1.5 с | $30–100 |
| O1 | CH читает Parquet в GCS (`gcs()`) + refreshable MV | 1–5 с / 10–50 мс | CH $50–160 |
| O2 | ClickPipes GCS → MergeTree + инкрементальные MV | 10–100 мс | CH $50–870 + ~$37 |
| O3 | BigQuery (dbt) → экспорт витрин → CH serving | 10–100 мс | CH + оркестрация |
| O4 | BigQuery ClickPipe (preview, только full load) | 10–100 мс | цена не опубликована |
| O5 | Dataflow BigQuery→ClickHouse template | 10–100 мс | CH + ~$1/запуск |
| O6 | BigQuery Iceberg (Lakehouse catalog) → CH DataLakeCatalog + refreshable MV | 0.3–2 с / 10–50 мс | GCS + CH $50–160 |
Рекомендация: для экзамена — O0; для DEJAP — O3 (один источник правды в BigQuery + быстрый serving в CH), O6 — как демонстрационный модуль open lakehouse.
