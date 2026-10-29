---
audience: "Data engineers, готовящиеся к Google Cloud Associate Data Practitioner (ADP)"
purpose: "Пробный экзамен ADP в условиях, максимально близких к реальным: 60 сценарных вопросов на английском, разбор на русском"
goal: "Выбирать сервис или настройку GCP по бизнес-ограничениям (стоимость, ops-нагрузка, задержка, безопасность) во всех четырёх доменах exam guide v1.0"
context: "Exam guide v1.0: 50–60 вопросов, 2 часа, домены S1 30% · S2 27% · S3 18% · S4 25%. Создан в проекте MyCerts; история создания, промпты и решения — в context/"
prerequisites: "6+ месяцев работы с данными в Google Cloud (рекомендация Google)"
duration_min: 120
---

Тест 11. Google Cloud Associate Data Practitioner (ADP) — пробный экзамен

60 вопросов, 120 минут, как на экзамене. Домены: S1 Data preparation and ingestion — 18, S2 Data analysis and presentation — 16, S3 Data pipeline orchestration — 11, S4 Data management — 15. Уровни: 🟩 знание/понимание — 17, 🟨 применение — 34, 🟥 анализ — 9. Сложность: простой — 20, средний — 31, сложный — 9. Вопросы 3, 6, 9, 32, 42, 55, 60 — с несколькими ответами (Choose two).

---

Вопрос 1 🟨 применение · средний
Your company receives daily CSV and Parquet files from 12 suppliers. New files are read several times during the first week; files older than 90 days are rarely read but must be kept for two years for reprocessing. You need to keep the original files unmodified at the lowest overall cost. What should you do?

---

* А) Store all files in a Cloud Storage bucket with the Archive class from the moment they arrive
* Б) Load the files into BigQuery and rely on time travel to recover earlier versions
* В) Keep the files on a Persistent Disk and take daily snapshots
* Г) Store the files in Cloud Storage with a lifecycle rule moving objects older than 90 days to Coldline ✅

Подсказка: Сравните, как часто читают свежие и старые файлы, и сколько стоит чтение из «холодных» классов.

Тема: S1 Data preparation and ingestion

Разбор: S1/S4 (1.2, 4.2). Свежие файлы читают часто — им нужен Standard, а после 90 дней подходит Coldline (минимальный срок хранения 90 дней, плата за чтение невелика при редком доступе). Archive с первого дня даёт плату за каждое чтение в первую неделю. Time travel в BigQuery хранит максимум 7 дней, Persistent Disk дороже и не масштабируется как хранилище файлов.

Вопрос 2 🟨 применение · средний
Your `events` table grows by 50 GB per day. Events can arrive up to three days after they occur. Most queries filter on the date the event occurred and cover the last seven days. You want to minimize query costs. How should you design the table?

---

* А) Use ingestion-time partitioning and filter on `_PARTITIONTIME`
* Б) Use integer-range partitioning on `store_id`
* В) Partition by day on `DATE(event_timestamp)` ✅
* Г) Create a table per day (`events_20261006`) and query with wildcard tables

Подсказка: По какому полю фильтруют запросы и куда попадёт событие, пришедшее через три дня?

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). Партиция по дате события совпадает с фильтром запросов, и опоздавшее событие попадает в свою дату. Ingestion-time положит его в день загрузки, и фильтр по дате события не отсечёт партиции. Шардирование по дням — антипаттерн (лимиты, метаданные, нет единой схемы). store_id не совпадает с фильтром.

Вопрос 3 🟨 применение · средний
An analyst must run queries in project `analytics-prj` and read tables only in the `sales` dataset. Following the principle of least privilege, which two roles should you grant? (Choose two.)

---

* ☑ ✅ BigQuery Job User on the project
* ☐ BigQuery Admin on the project
* ☑ ✅ BigQuery Data Viewer on the `sales` dataset
* ☐ Editor on the project
* ☐ BigQuery Data Editor on the project

Тема: S4 Data management

Разбор: S4 (4.1). Job User разрешает запускать запросы, Data Viewer на датасете — читать только его таблицы. Admin, Editor и Data Editor на проекте дают лишние права (запись, все датасеты, другие сервисы).

Вопрос 4 🟨 применение · простой
A mobile app publishes JSON clickstream events to a Pub/Sub topic. The message fields match the target BigQuery table, and no transformation is required. You need to write the events to BigQuery with the lowest operational overhead. What should you do?

---

* А) Create a BigQuery subscription on the topic that writes by using the table schema ✅
* Б) Deploy the Dataflow "Pub/Sub to BigQuery" template
* В) Write a Cloud Run function that inserts each event with the Storage Write API
* Г) Consume a pull subscription from a managed instance group on Compute Engine

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). BigQuery subscription пишет сообщения прямо в таблицу — нет пайплайна, который надо запускать и мониторить. Dataflow-шаблон тоже работает, но это отдельные воркеры и задание. Cloud Run и Compute Engine — свой код и инфраструктура.

Вопрос 5 🟩 понимание · простой
A vendor writes new files to an Amazon S3 bucket every night. You need to copy only new or changed files to Cloud Storage once a day, with minimal custom code and no infrastructure to maintain. What should you do?

---

* А) Write a Cloud Run job that runs `gcloud storage rsync`, triggered by Cloud Scheduler
* Б) Create a daily Storage Transfer Service job from S3 to Cloud Storage ✅
* В) Order a Transfer Appliance and ship it to the vendor every month
* Г) Create a BigQuery Data Transfer Service transfer from S3 into BigQuery

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.1). Storage Transfer Service — управляемый перенос S3 → GCS по расписанию, копирует только новые и изменённые объекты. Cloud Run + rsync работает, но это свой код. BigQuery DTS из S3 грузит в таблицу BigQuery, а не в bucket. Transfer Appliance — для разовых переносов сотен терабайт.

Вопрос 6 🟨 применение · средний
Analysts sometimes run queries without a date filter against a 30 TB date-partitioned table, which causes unexpected on-demand charges. You need to prevent full-table scans and limit how much each analyst can spend per day. Which two actions should you take? (Choose two.)

---

* ☐ Set a partition expiration of 90 days on the table
* ☑ ✅ Set `require_partition_filter` to TRUE on the table
* ☐ Enable BI Engine for the project
* ☑ ✅ Create a custom quota for query usage per day per user
* ☐ Re-create the table as an external table over Parquet files

Подсказка: Одно действие касается таблицы, другое — лимитов проекта.

Тема: S2 Data analysis and presentation

Разбор: S2/S4 (2.1, 4.1). `require_partition_filter` отклоняет запросы без фильтра по партиции, а custom quota «Query usage per day per user» ограничивает объём, который пользователь сканирует за день. Expiration удаляет данные, BI Engine ускоряет, но не ограничивает, external table не уменьшает сканирование.

Вопрос 7 🟩 понимание · простой
Your security team requires that access to a Cloud Storage bucket be controlled only through IAM, and object ACLs must not be used. What should you do?

---

* А) Enable uniform bucket-level access on the bucket ✅
* Б) Remove the `allUsers` ACL from each object
* В) Enable Object Versioning
* Г) Set a retention policy on the bucket

Тема: S4 Data management

Разбор: S4 (4.1). Uniform bucket-level access отключает ACL и оставляет только IAM. Удаление отдельных ACL не мешает добавить новые; versioning и retention к доступу не относятся.

Вопрос 8 🟨 применение · средний
Your application uses Cloud SQL for PostgreSQL. Analysts need the `orders` and `customers` tables in BigQuery, with inserts, updates, and deletes reflected within minutes. The solution must minimize load on the source database and require minimal custom code. What should you do?

---

* А) Query the source tables from dashboards with BigQuery federated queries (`EXTERNAL_QUERY`)
* Б) Export the tables to CSV in Cloud Storage every hour and load them into BigQuery
* В) Create a Datastream stream from Cloud SQL for PostgreSQL to BigQuery ✅
* Г) Replicate to a second Cloud SQL instance with Database Migration Service and query it federatedly

Подсказка: Нужны изменения (включая DELETE) с задержкой в минуты и без нагрузки на источник.

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Datastream читает логическую репликацию (CDC) и пишет в BigQuery с задержкой в минуты, почти не нагружая базу. EXTERNAL_QUERY нагружает источник каждым запросом дашборда. Почасовой экспорт CSV не даёт минутной задержки и теряет DELETE. Database Migration Service нужен для миграции базы, а не для аналитики.

Вопрос 9 🟥 анализ · сложный
You must calculate per-store sales totals in 1-minute windows from a Pub/Sub stream, based on the time each sale occurred. About 10% of events arrive up to 5 minutes late and must be counted in the correct window. Results go to BigQuery. You want a managed, serverless solution. Which two actions should you take? (Choose two.)

---

* ☑ ✅ Build a Dataflow streaming pipeline with fixed event-time windows
* ☐ Enable message ordering on the Pub/Sub subscription
* ☑ ✅ Configure allowed lateness and triggers so late events update their window
* ☐ Use processing-time windows so late events go into the currently open window
* ☐ Run Spark Structured Streaming on a long-running Dataproc cluster

Подсказка: Окно должно определяться временем события, а не временем прихода; подумайте, что делать с опоздавшими.

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.1). Event-time окна в Dataflow + allowed lateness и триггеры — стандартное решение для опоздавших событий. Ordering keys упорядочивают доставку, но не возвращают опоздавшие события в прошлое окно. Processing-time окна кладут событие не в ту минуту. Dataproc — не serverless и требует управления кластером.

Вопрос 10 🟨 применение · простой
Transaction timestamps are stored in a TIMESTAMP column, `transaction_ts`. The finance team in Tbilisi (UTC+4) reports revenue by local calendar day, and their daily totals do not match your report. Which expression should you use to group revenue by day?

---

* А) `DATE(transaction_ts, 'Asia/Tbilisi')` ✅
* Б) `DATE(transaction_ts)`
* В) `DATETIME(transaction_ts)`
* Г) `TIMESTAMP_TRUNC(transaction_ts, DAY)`

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). TIMESTAMP хранит момент в UTC; `DATE(ts, tz)` берёт календарную дату в нужном часовом поясе. Без пояса `DATE` и `TIMESTAMP_TRUNC(…, DAY)` режут сутки по UTC, а `DATETIME` даёт не дату, а дату-время в UTC.

Вопрос 11 🟨 применение · средний
You must ensure that no bucket in any project of your organization can ever be made publicly accessible, including by project owners. What should you do?

---

* А) Grant Storage Admin only to the security team
* Б) Enforce the `storage.publicAccessPrevention` organization policy constraint ✅
* В) Enable uniform bucket-level access on existing buckets
* Г) Audit bucket permissions weekly with Cloud Asset Inventory

Тема: S4 Data management

Разбор: S4 (4.1). Org policy `storage.publicAccessPrevention` запрещает публичный доступ для всех текущих и будущих бакетов и не может быть отменена на уровне проекта. Роли и UBLA не мешают выдать `allUsers` через IAM, аудит только находит проблему постфактум.

Вопрос 12 🟩 понимание · простой
You store three years of transaction history (about 40 TB) in Cloud Storage for occasional analysis from BigQuery and Spark. Most queries read 5–8 of the 60 columns. You want to minimize storage size and data scanned. Which file format should you use?

---

* А) CSV compressed with gzip
* Б) Newline-delimited JSON
* В) Apache Avro
* Г) Apache Parquet ✅

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Parquet — колоночный формат: читаются только нужные колонки, сжатие лучше. Avro компактный и со схемой, но строчный — BigQuery читает из него все колонки. CSV и JSON — самые объёмные и без схемы.

Вопрос 13 🟨 применение · простой
Within each daily partition of a sales table, most queries filter on `customer_id` (about 2 million distinct values), and some also filter on `country`. You need to further reduce data scanned without changing the queries. What should you do?

---

* А) Change the table to integer-range partitioning on `customer_id`
* Б) Cluster the table by `customer_id` and `country` ✅
* В) Create a separate table for each country
* Г) Create a logical view that filters on `customer_id`

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). Кластеризация сортирует данные внутри партиций и позволяет пропускать блоки. Партиций может быть не больше 10 000, а 2 млн значений столько не дадут. Таблицы по странам потребуют менять запросы, logical view не уменьшает сканирование.

Вопрос 14 🟨 применение · средний
An external auditor without a Google account must download one report file from a private Cloud Storage bucket during the next 24 hours. What should you do?

---

* А) Make the object public and send its URL
* Б) Grant `allUsers` the Storage Object Viewer role on the bucket
* В) Generate a signed URL for the object that expires in 24 hours ✅
* Г) Copy the file to a public bucket

Тема: S4 Data management

Разбор: S4 (4.1). Signed URL даёт временный доступ к одному объекту без учётной записи Google. Публичный объект или бакет открывает данные всем и без срока.

Вопрос 15 🟩 понимание · простой
Your team writes SQL transformations in BigQuery that depend on each other. They want dependency management, Git version control, and data assertions, without leaving BigQuery or managing infrastructure. Which tool should you use?

---

* А) Dataform ✅
* Б) Cloud Data Fusion
* В) Dataflow
* Г) Dataproc

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.1). Dataform — SQLX-модели в BigQuery с графом зависимостей, git и assertions (аналог dbt). Data Fusion — визуальный ETL, Dataflow и Dataproc — обработка кодом, а не управление SQL-моделями.

Вопрос 16 🟥 анализ · сложный
Your team stores daily Parquet exports in Cloud Storage. Analysts query the latest 90 days many times per day from Looker Studio dashboards that must respond as fast as possible. The data is used only from BigQuery and is updated once per day. Only authorized users may see the `margin` column. What should you do?

---

* А) Create a BigLake table with metadata caching and apply a policy tag to `margin`
* Б) Load the files daily into a partitioned native table and apply a policy tag to `margin` ✅
* В) Create an external table over the files and share the dataset with the analysts
* Г) Convert the files to ORC with Dataproc and query them with Spark SQL

Подсказка: Требованию безопасности отвечают два варианта; решает требование к скорости и то, что данные нужны только BigQuery.

Тема: S1 Data preparation and ingestion

Разбор: S1/S4 (1.2, 4.1). Нативная партиционированная таблица — минимальная задержка, кеш результатов и BI Engine; policy tag закрывает колонку. BigLake тоже поддерживает policy tags и нужен, когда данные должны остаться в GCS для других движков, но он медленнее. Обычная external table не поддерживает column-level security. Spark SQL из дашборда — лишняя инфраструктура и задержка.

Вопрос 17 🟨 применение · средний
A Looker Studio dashboard runs the same SUM and COUNT by day and region every few minutes against an append-only 2 TB table that receives data continuously. You want lower latency and cost, always up-to-date results, and minimal maintenance. What should you do?

---

* А) Create a scheduled query that rebuilds a summary table every hour
* Б) Create a logical view with the aggregation
* В) Export the aggregates to Cloud SQL every 15 minutes
* Г) Create a materialized view with the aggregation ✅

Подсказка: Решение должно быть одновременно свежим и не требовать обслуживания.

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). Materialized view обновляется инкрементально, а при запросе BigQuery добавляет ещё не учтённые строки, поэтому результат всегда актуален. Scheduled query отстаёт до часа, logical view не ускоряет, экспорт в Cloud SQL — лишний пайплайн и задержка.

Вопрос 18 🟩 понимание · простой
Analysts need to run ad hoc SQL aggregations over 5 TB of sales history and join it with product data updated daily. The team does not want to manage indexes, servers, or capacity. Which storage solution should you use?

---

* А) Cloud SQL for PostgreSQL with two read replicas
* Б) Bigtable
* В) Spanner
* Г) BigQuery ✅

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). BigQuery — serverless-хранилище для аналитики. Cloud SQL и Spanner рассчитаны на транзакции, Bigtable — key-value без SQL-джойнов.

Вопрос 19 🟨 применение · средний
Your company wants to share curated BigQuery datasets with dozens of partner organizations. Partners must query the latest data from their own projects, without copies, and you want to manage subscriptions centrally. What should you do?

---

* А) Export the datasets to Cloud Storage and share the bucket
* Б) Copy the datasets to each partner's project every night
* В) Email CSV extracts to the partners weekly
* Г) Publish the datasets as listings in an Analytics Hub exchange ✅

Тема: S4 Data management

Разбор: S4 (4.1). Analytics Hub публикует listings: подписчик получает linked dataset в своём проекте, данные не копируются и всегда актуальны, издатель видит подписки. Экспорт, копии и CSV устаревают и плодят копии.

Вопрос 20 🟩 понимание · простой
Every morning you need to run one SQL statement that aggregates yesterday's orders into a summary table. There are no other dependencies. You want the simplest solution with the lowest cost. What should you do?

---

* А) Create a Cloud Composer environment with a daily DAG
* Б) Create a BigQuery scheduled query ✅
* В) Run a cron job on a Compute Engine VM that calls `bq query`
* Г) Build a Dataflow batch pipeline triggered by Cloud Scheduler

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Scheduled query (на базе BigQuery DTS) — встроенное расписание одного запроса без инфраструктуры. Composer — постоянная среда и заметная стоимость, VM нужно обслуживать, Dataflow избыточен.

Вопрос 21 🟩 понимание · простой
A product dashboard shows daily active users from a 20-billion-row events table. Product managers accept a small statistical error in exchange for faster and cheaper queries. Which function should you use?

---

* А) `APPROX_COUNT_DISTINCT(user_id)` ✅
* Б) `COUNT(DISTINCT user_id)`
* В) `COUNT(user_id)`
* Г) `SUM(1)` with `GROUP BY user_id`

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). `APPROX_COUNT_DISTINCT` использует HyperLogLog++ и работает быстрее точного подсчёта с небольшой погрешностью. `COUNT(DISTINCT)` точный, но дороже; `COUNT(user_id)` считает события, а не пользователей.

Вопрос 22 🟨 применение · средний
Your team loads raw JSON order events into BigQuery staging tables every hour. Cleaning rules change often, and SQL-savvy analysts want to change the transformations themselves and reprocess history without reloading the source files. Which approach should you use?

---

* А) ETL: transform the events in Dataflow before loading them
* Б) ELT: keep raw data in BigQuery and transform it in SQL, for example with Dataform ✅
* В) ETL: clean the files in a Cloud Data Fusion pipeline before loading
* Г) Transform the events in the source application before publishing

Подсказка: Кто меняет логику и где лежат сырые данные для повторной обработки?

Тема: S1 Data preparation and ingestion

Разбор: S1/S3 (1.1, 3.1). При ELT сырые данные уже в BigQuery, аналитики правят SQL и пересчитывают историю без повторной загрузки. В ETL-вариантах изменение логики требует правки пайплайна и повторного чтения исходных файлов.

Вопрос 23 🟨 применение · средний
Audit logs are written to Cloud Storage. They are read about once per quarter during audits and must be kept for one year. You want the lowest storage cost without retrieval penalties for that access pattern. Which storage class should you use?

---

* А) Standard
* Б) Nearline
* В) Coldline ✅
* Г) Archive

Тема: S4 Data management

Разбор: S4 (4.2). Coldline рассчитан на доступ реже раза в квартал (минимальный срок 90 дней). Nearline — для доступа раз в месяц и дороже в хранении, Archive — раз в год, с минимальным сроком 365 дней и самой дорогой выборкой.

Вопрос 24 🟨 применение · средний
A CDC feed writes every change of a customer record to `customer_changes` (`customer_id`, `updated_at`, and 30 other columns); `updated_at` is unique per customer. Analysts need only the latest version of each customer, with all columns. Which query should you use?

---

* А) `SELECT DISTINCT * FROM customer_changes`
* Б) `SELECT customer_id, MAX(updated_at) FROM customer_changes GROUP BY customer_id`
* В) `SELECT * FROM customer_changes QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY updated_at DESC) = 1` ✅
* Г) `SELECT * FROM customer_changes ORDER BY updated_at DESC LIMIT 1`

Подсказка: Нужна одна строка на клиента и все колонки.

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). `ROW_NUMBER` с `QUALIFY` оставляет последнюю версию каждого клиента со всеми колонками. DISTINCT оставит все версии, GROUP BY вернёт только две колонки, LIMIT 1 — одну строку на всю таблицу.

Вопрос 25 🟩 понимание · простой
The marketing team needs Google Ads campaign data in BigQuery every day, including a six-month backfill. You want a managed solution with the least development effort. What should you do?

---

* А) Configure a BigQuery Data Transfer Service transfer for Google Ads and run a backfill ✅
* Б) Build a Cloud Run job that calls the Google Ads API on a schedule
* В) Copy Google Ads reports to Cloud Storage with Storage Transfer Service
* Г) Replicate Google Ads data with Datastream

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). У BigQuery DTS есть коннектор Google Ads с расписанием и backfill. Cloud Run — свой код, Storage Transfer Service переносит файлы, а не данные Ads, Datastream работает только с базами данных.

Вопрос 26 🟨 применение · средний
You are migrating 200 existing Apache Airflow DAGs from an on-premises server. The DAGs coordinate Dataproc, BigQuery, and Cloud Storage tasks with retries and backfills. You want to minimize code changes. Which service should you use?

---

* А) Workflows
* Б) BigQuery scheduled queries
* В) Cloud Composer ✅
* Г) Dataproc Workflow Templates

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Cloud Composer — управляемый Airflow: DAG переносятся почти без изменений, есть операторы GCP, retries и backfill. Workflows и шаблоны Dataproc потребуют переписать логику; scheduled queries не оркестрируют разные сервисы.

Вопрос 27 🟩 понимание · простой
A bucket with Object Versioning enabled keeps growing. You must delete objects older than 365 days and noncurrent versions 30 days after they become noncurrent, automatically. What should you do?

---

* А) Write a Cloud Run job that lists and deletes old objects daily
* Б) Add lifecycle rules: Delete when age is 365 days, and Delete when daysSinceNoncurrentTime is 30 ✅
* В) Set a retention policy of 365 days
* Г) Disable Object Versioning

Тема: S4 Data management

Разбор: S4 (4.2). Object Lifecycle Management удаляет объекты по условиям age и daysSinceNoncurrentTime без своего кода. Retention policy наоборот запрещает удаление, отключение versioning не удаляет старые версии.

Вопрос 28 🟨 применение · средний
A Dataflow pipeline exchanges records with other teams through Cloud Storage. Records are written and consumed one row at a time, producers often add optional fields, and consumers must read old and new files without failures. You need a compact binary format with an embedded schema. Which format should you choose?

---

* А) CSV with a header row
* Б) JSON Lines
* В) Apache Avro ✅
* Г) Apache Parquet

Подсказка: Важны построчная запись и эволюция схемы, а не чтение отдельных колонок.

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Avro — строчный бинарный формат со схемой в файле и правилами эволюции (новые поля с default). Parquet колоночный: удобен для аналитики, но неудобен для построчной записи. CSV и JSON без бинарного сжатия и схемы.

Вопрос 29 🟨 применение · средний
Several departments build their own reports, and revenue is calculated differently in each. You need a single governed definition of metrics, reusable across dashboards, with changes reviewed in version control. Which tool should you use?

---

* А) Looker Studio with calculated fields in each report
* Б) Looker with metrics defined in LookML ✅
* В) Connected Sheets on BigQuery
* Г) Colab Enterprise notebooks shared with the departments

Тема: S2 Data analysis and presentation

Разбор: S2 (2.2). Looker даёт семантический слой: метрики описаны один раз в LookML, проект хранится в git. Вычисляемые поля Looker Studio живут в каждом отчёте отдельно; Sheets и ноутбуки не дают управляемой модели.

Вопрос 30 🟩 понимание · простой
Tables in the `staging` BigQuery dataset are temporary and must be deleted automatically 7 days after creation. What should you do?

---

* А) Set a default table expiration of 7 days on the `staging` dataset ✅
* Б) Set a partition expiration of 7 days on each table
* В) Create a scheduled query that runs `DROP TABLE` statements
* Г) Rely on time travel to remove old tables

Тема: S4 Data management

Разбор: S4 (4.2). Default table expiration датасета задаёт срок жизни всем новым таблицам. Partition expiration удаляет партиции, но не таблицы; scheduled DROP — свой код; time travel хранит историю, а не удаляет.

Вопрос 31 🟨 применение · средний
A nightly process calls a Cloud Run service, then starts a BigQuery load job through its API, and finally sends an HTTP notification. You want a serverless orchestrator that is billed per execution and needs no always-on environment. Which service should you use?

---

* А) Workflows ✅
* Б) Cloud Composer
* В) A Compute Engine VM running cron
* Г) Dataproc Workflow Templates

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Workflows — serverless-оркестрация HTTP/API-шагов с оплатой за шаги. Composer работает постоянно и дорог для трёх вызовов, VM нужно обслуживать, шаблоны Dataproc — только для заданий Dataproc.

Вопрос 32 🟨 применение · средний
A supplier's daily files sometimes contain malformed records (invalid dates, missing required fields). Auditors require every received record to be retained, and the data team must be able to review and correct rejected records. Which two actions should you take? (Choose two.)

---

* ☑ ✅ Keep the original files unmodified in Cloud Storage
* ☐ Load directly into the reporting table with a high `max_bad_records` value
* ☐ Correct the records manually and overwrite the original files
* ☑ ✅ Write records that fail validation to a separate error table with the failure reason
* ☐ Load every column as STRING into the reporting table

Подсказка: Одно действие сохраняет исходные данные, другое делает ошибки видимыми.

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.1). Неизменный raw-слой выполняет требование аудита и позволяет переобработку, а dead-letter таблица с причиной ошибки даёт команде список для исправления. `max_bad_records` молча теряет строки, перезапись исходников нарушает аудит, всё в STRING переносит проблему в отчёты.

Вопрос 33 🟨 применение · средний
Analysts need a new "Total Revenue" metric in a Looker Explore, calculated as the sum of the `revenue` column of the `orders` view. What should you do?

---

* А) Add a dimension of `type: sum` to the model file
* Б) Add a calculated field in each Looker Studio report
* В) Add a measure with `type: sum` and `sql: ${TABLE}.revenue` to the `orders` view ✅
* Г) Add a `total_revenue` column to the BigQuery table

Тема: S2 Data analysis and presentation

Разбор: S2 (2.2). Агрегаты в LookML — это measures во view-файле: `measure: total_revenue { type: sum sql: ${TABLE}.revenue ;; }`. У dimension нет типа sum; поле в Looker Studio и колонка в таблице обходят модель.

Вопрос 34 🟥 анализ · сложный
Regulations require that trade records be stored for 7 years in a way that nobody, including administrators, can delete or overwrite them before the period ends. The records are almost never read. What should you do?

---

* А) Store the records in an Archive class bucket with Object Versioning enabled
* Б) Store the records in BigQuery and restrict the Data Editor role
* В) Store the records in a Coldline bucket and remove delete permissions from all users
* Г) Store the records in an Archive class bucket with a 7-year retention policy, and lock the policy ✅

Тема: S4 Data management

Разбор: S4 (4.2). Bucket Lock (заблокированная retention policy) — WORM: объект нельзя удалить или перезаписать до конца срока, и саму политику уже нельзя ослабить. Archive — самый дешёвый класс для почти не читаемых данных. Versioning и IAM администратор может изменить.

Вопрос 35 🟨 применение · средний
Your company must move 400 TB of archived data from an on-premises data center to Cloud Storage within four weeks. The data center has a shared 100 Mbps internet connection that cannot be saturated. What should you do?

---

* А) Use Storage Transfer Service with on-premises transfer agents
* Б) Order a Transfer Appliance, copy the data to it, and ship it to Google ✅
* В) Run `gcloud storage cp` in parallel from several on-premises servers
* Г) Use BigQuery Data Transfer Service to load the files directly into BigQuery

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.1). 100 Мбит/с — около 1 ТБ в сутки в идеале, то есть больше года на 400 ТБ. Transfer Appliance — физическое устройство для сотен терабайт за недели. Агенты STS и gcloud упираются в тот же канал, BigQuery DTS не переносит файлы с on-prem.

Вопрос 36 🟥 анализ · сложный
You built a Looker Studio report on a BigQuery table. An external partner must view the report, but must not get any access to your BigQuery project. What should you do?

---

* А) Set the data source credentials to the owner's credentials and share the report with the partner ✅
* Б) Set the data source credentials to the viewer's credentials and share the report
* В) Grant the partner the BigQuery Data Viewer role on the dataset
* Г) Export the table to Google Sheets and share the spreadsheet

Тема: S2 Data analysis and presentation

Разбор: S2 (2.2). С owner's credentials запросы идут от владельца источника, и зрителю не нужны права в BigQuery. Viewer's credentials потребуют у партнёра доступ к данным, роль Data Viewer — это и есть доступ к проекту, а экспорт в Sheets теряет актуальность и контроль.

Вопрос 37 🟨 применение · средний
When a partner uploads a file to a Cloud Storage bucket, a Cloud Run service must start processing it immediately. You want an event-driven solution with no polling. What should you do?

---

* А) Schedule Cloud Scheduler to call the service every minute to list new files
* Б) Create an Eventarc trigger on the `google.cloud.storage.object.v1.finalized` event that targets the Cloud Run service ✅
* В) Use a Cloud Composer sensor that waits for new objects
* Г) Run a Dataflow streaming pipeline that lists the bucket

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Eventarc доставляет событие finalize объекта в Cloud Run без опроса. Scheduler, сенсор Composer и листинг из Dataflow — это polling с задержкой и лишней стоимостью.

Вопрос 38 🟥 анализ · сложный
Analytics jobs run in us-east1 and us-east4. Raw data in Cloud Storage must stay available if one region fails, and new objects must be replicated to the second region within 15 minutes. You want the lowest latency for compute in both regions. Which storage configuration should you use?

---

* А) A multi-region bucket in US
* Б) A regional bucket in us-east1 with daily copies to us-east4 by Storage Transfer Service
* В) A dual-region bucket in us-east1 and us-east4 with turbo replication ✅
* Г) Zonal Persistent Disks in both regions replicated by a cron job

Тема: S1 Data preparation and ingestion

Разбор: S1/S4 (1.2, 4.3). Dual-region с выбранной парой регионов даёт низкую задержку из обоих регионов, а turbo replication гарантирует RPO 15 минут. Multi-region US не позволяет выбрать регионы и без turbo реплицирует до 12 часов. Ежедневное копирование не даёт 15 минут, диски — не хранилище объектов.

Вопрос 39 🟥 анализ · сложный
A critical BigQuery table is sometimes corrupted by faulty jobs. You must be able to restore the table to its state on any day in the last 30 days, with the lowest cost and effort. What should you do?

---

* А) Increase the dataset's time travel window to 30 days
* Б) Create a daily table snapshot with a 30-day expiration, for example with a scheduled query ✅
* В) Rely on fail-safe storage to recover the table
* Г) Export the full table to Cloud Storage as CSV every day

Тема: S4 Data management

Разбор: S4 (4.3). Time travel — максимум 7 дней, fail-safe — ещё 7 дней и только через поддержку. Table snapshot хранит только отличия от базовой таблицы и восстанавливается одной командой. Полный CSV-экспорт дороже и восстанавливается дольше.

Вопрос 40 🟩 понимание · простой
A data analyst wants to explore BigQuery data in Python notebooks with BigQuery DataFrames. The notebooks must use managed runtimes, be shared through IAM, and require no infrastructure management. Which product should you use?

---

* А) Jupyter on a Compute Engine VM
* Б) Colab Enterprise ✅
* В) Jupyter on a Dataproc cluster
* Г) Jupyter installed on the analyst's laptop

Тема: S2 Data analysis and presentation

Разбор: S2 (2.1). Colab Enterprise — управляемые ноутбуки в Google Cloud с IAM, встроенные в BigQuery Studio. Остальные варианты требуют обслуживать VM, кластер или ноутбук.

Вопрос 41 🟨 применение · средний
You store millions of product images in Cloud Storage. Analysts want to filter images by metadata (size, upload date) with SQL in BigQuery and run a Vertex AI model on them without moving the files. What should you do?

---

* А) Load the images into a BigQuery table as BYTES columns
* Б) Store the images in Bigtable and query them with federated queries
* В) Store image metadata in Firestore and export it to BigQuery nightly
* Г) Create a BigQuery object table over the Cloud Storage bucket ✅

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Object table — таблица метаданных неструктурированных объектов в GCS; по ней можно писать SQL и вызывать модели (ML.PREDICT / remote models), не перемещая файлы. BYTES в BigQuery дорого и ограничено по размеру строки, Bigtable и Firestore тут лишние.

Вопрос 42 🟥 анализ · сложный
A Dataflow streaming pipeline that reads from Pub/Sub is falling behind, and dashboards show stale data. You need to find where the delay comes from. Which two actions should you take? (Choose two.)

---

* ☐ Check the Cloud Billing report for the Dataflow job
* ☑ ✅ Check the Data freshness and System latency metrics on the job's metrics tab
* ☐ Delete and recreate the Pub/Sub subscription
* ☑ ✅ Open the job graph and compare wall time and throughput of each step
* ☐ Change the Pub/Sub topic schema

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). В Dataflow job UI data freshness и system latency показывают величину отставания, а граф с wall time по шагам показывает узкое место (например, медленный ParDo или горячий ключ). Billing не диагностирует, пересоздание подписки теряет сообщения, схема топика ни при чём.

Вопрос 43 🟨 применение · средний
A Cloud SQL for PostgreSQL instance must fail over automatically if its zone becomes unavailable, with no data loss. What should you do?

---

* А) Create a read replica in another zone
* Б) Enable automated daily backups
* В) Enable the high availability (regional) configuration ✅
* Г) Export the database to Cloud Storage every hour

Тема: S4 Data management

Разбор: S4 (4.3). HA-конфигурация держит standby в другой зоне с синхронной репликацией и переключается автоматически. Read replica не переключается сама, бэкапы и экспорт дают потерю данных и ручное восстановление.

Вопрос 44 🟩 понимание · простой
You want to predict whether a customer will cancel a subscription (yes/no) by using historical data in BigQuery, with SQL only. Which model type should you use in `CREATE MODEL`?

---

* А) `LINEAR_REG`
* Б) `KMEANS`
* В) `ARIMA_PLUS`
* Г) `LOGISTIC_REG` ✅

Тема: S2 Data analysis and presentation

Разбор: S2 (2.3). Отток да/нет — бинарная классификация: `LOGISTIC_REG` (или BOOSTED_TREE_CLASSIFIER). LINEAR_REG предсказывает число, KMEANS — кластеризация без меток, ARIMA_PLUS — прогноз временных рядов.

Вопрос 45 🟩 понимание · простой
A fleet of IoT devices writes 500,000 telemetry records per second. The application must read the latest readings for a device with single-digit-millisecond latency. Which storage solution should you use?

---

* А) Bigtable ✅
* Б) BigQuery
* В) Cloud SQL for MySQL
* Г) Cloud Storage

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Bigtable — wide-column NoSQL для огромного потока записей и чтения по ключу (device#timestamp) за миллисекунды. BigQuery — аналитика, а не точечные чтения; Cloud SQL не выдержит такой поток записей; GCS не даёт чтений по ключу.

Вопрос 46 🟨 применение · средний
Your Cloud SQL database already uses the high availability configuration. The business now requires recovery within an hour if the entire region becomes unavailable, losing at most a few minutes of data. What should you add?

---

* А) A second HA instance in the same region
* Б) A cross-region read replica that can be promoted during a disaster ✅
* В) Point-in-time recovery in the same region
* Г) Weekly exports to a multi-region bucket

Тема: S4 Data management

Разбор: S4 (4.3). Cross-region replica асинхронно отстаёт на минуты и повышается до primary при потере региона. HA и PITR работают в пределах региона, еженедельный экспорт даёт до недели потерь.

Вопрос 47 🟨 применение · средний
You need to forecast daily sales for each of 300 stores for the next 30 days, using two years of history in BigQuery, with the least effort. What should you do?

---

* А) Train an `ARIMA_PLUS` model with `time_series_id_col = 'store_id'` and call `ML.FORECAST` ✅
* Б) Train 300 separate `LINEAR_REG` models, one per store
* В) Train a `KMEANS` model and use cluster centroids as forecasts
* Г) Export the data to Cloud Storage and train a custom model on Compute Engine

Тема: S2 Data analysis and presentation

Разбор: S2 (2.3). ARIMA_PLUS с `time_series_id_col` обучает много рядов одной командой, а `ML.FORECAST` строит прогноз на горизонт. 300 регрессий — лишняя работа без учёта сезонности; KMEANS не прогнозирует; своя модель противоречит «least effort».

Вопрос 48 🟩 понимание · простой
A BigQuery load job failed last night, and you need to read the detailed error messages for that job. Where should you look first?

---

* А) Cloud Trace
* Б) Cloud Profiler
* В) Cloud Logging (Logs Explorer), filtered by the BigQuery resource and severity ERROR ✅
* Г) Security Command Center

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Ошибки заданий BigQuery попадают в Cloud Logging (а также видны в истории заданий и INFORMATION_SCHEMA.JOBS). Trace и Profiler — для задержек и профилирования приложений, Security Command Center — для угроз безопасности.

Вопрос 49 🟩 понимание · простой
A team of business analysts without programming experience must build pipelines that extract data from on-premises Oracle and SQL Server databases, clean it, and load it into BigQuery. They want a visual, drag-and-drop interface. Which service should you use?

---

* А) Dataflow with a custom Apache Beam pipeline
* Б) Dataproc with Spark jobs
* В) Cloud Data Fusion ✅
* Г) Cloud Composer with Python DAGs

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.1). Cloud Data Fusion — визуальный конструктор пайплайнов (CDAP) с готовыми коннекторами к базам данных. Dataflow, Dataproc и Composer требуют писать код.

Вопрос 50 🟨 применение · средний
Compliance requires that you control the rotation of the keys that encrypt your BigQuery datasets and that you can revoke access to the data by disabling a key. The keys may be stored in Google Cloud. What should you use?

---

* А) Google-managed encryption keys (default)
* Б) Customer-managed encryption keys (CMEK) in Cloud KMS ✅
* В) Customer-supplied encryption keys (CSEK)
* Г) Client-side encryption with keys stored on employees' laptops

Тема: S4 Data management

Разбор: S4 (4.4). CMEK — ключи в Cloud KMS под вашим управлением: ротация, отключение, уничтожение, аудит. GMEK ротирует Google без вашего контроля; CSEK не поддерживается для BigQuery и нужен, когда ключи нельзя хранить в Google Cloud; ключи на ноутбуках — риск.

Вопрос 51 🟩 понимание · простой
You trained a classification model with BigQuery ML. You now need to score 1 million new customer rows stored in a BigQuery table. Which function should you use?

---

* А) `ML.EVALUATE`
* Б) `ML.PREDICT` ✅
* В) `ML.TRAINING_INFO`
* Г) `ML.FEATURE_INFO`

Тема: S2 Data analysis and presentation

Разбор: S2 (2.3). `ML.PREDICT` выполняет инференс на новых строках. `ML.EVALUATE` считает метрики качества, `ML.TRAINING_INFO` показывает ход обучения, `ML.FEATURE_INFO` — статистику признаков.

Вопрос 52 🟨 применение · средний
You need to check BigQuery tables daily for null values in required columns, values out of range, and duplicate keys. Results must be visible in the console and must not require maintaining a custom pipeline. What should you do?

---

* А) Write a Dataflow pipeline that validates the tables and logs errors
* Б) Configure Dataplex data quality scans with rules on the tables ✅
* В) Create a Looker Studio report that highlights invalid values
* Г) Create a Cloud Monitoring uptime check for each table

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.1). Dataplex auto data quality — управляемые сканы с правилами (NOT NULL, диапазон, уникальность) по расписанию и результатами в консоли и BigQuery. Dataflow — свой код, Looker Studio только визуализирует, uptime checks проверяют доступность сервисов, а не данные.

Вопрос 53 🟨 применение · средний
The on-call engineer must be notified when the data freshness of a Dataflow streaming job exceeds 10 minutes. What should you do?

---

* А) Create a Looker Studio report that shows the job's metrics
* Б) Ask the engineer to check the Dataflow job UI every hour
* В) Create a log-based metric for successful records
* Г) Create a Cloud Monitoring alerting policy on the job's data freshness metric with a notification channel ✅

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Alerting policy в Cloud Monitoring по метрике freshness с порогом 10 минут и каналом (email, PagerDuty, Slack) — штатный способ. Отчёт и ручная проверка не оповещают, метрика по успешным записям не измеряет задержку.

Вопрос 54 🟥 анализ · сложный
A financial company requires that encryption keys for certain Cloud Storage objects are never stored in Google Cloud. Applications provide the key with every read and write request. Which option meets the requirement?

---

* А) Customer-supplied encryption keys (CSEK) ✅
* Б) CMEK with Cloud KMS keys
* В) CMEK with Cloud HSM keys
* Г) Google-managed encryption keys with annual rotation

Тема: S4 Data management

Разбор: S4 (4.4). CSEK — ключ передаётся с каждым запросом и Google его не хранит (только хеш). Cloud KMS и Cloud HSM хранят ключи в Google Cloud, GMEK полностью управляет Google.

Вопрос 55 🟥 анализ · сложный
You want to classify the sentiment of customer reviews stored in BigQuery by using a Gemini model, directly from SQL. Which two actions should you take? (Choose two.)

---

* ☑ ✅ Create a Cloud resource connection and grant its service account the Vertex AI User role
* ☐ Export the reviews to Cloud Storage and start a Vertex AI batch prediction job
* ☑ ✅ Create a remote model with `CREATE MODEL … REMOTE WITH CONNECTION` and call it with a generate-text function
* ☐ Train a `LOGISTIC_REG` model on the review text
* ☐ Deploy the Gemini model to a Vertex AI endpoint on dedicated GPUs

Тема: S2 Data analysis and presentation

Разбор: S2 (2.3). Для LLM из SQL нужны connection (её service account с ролью Vertex AI User) и remote model поверх Gemini, а затем `ML.GENERATE_TEXT` / `AI.GENERATE_TEXT`. Экспорт и batch prediction — не «из SQL»; LOGISTIC_REG требует размеченных данных; Gemini не разворачивают на своих GPU.

Вопрос 56 🟩 понимание · простой
You need to load a CSV file with a header row from Cloud Storage into a new BigQuery table and let BigQuery infer the schema. Which command should you use?

---

* А) `bq mk --external_table_definition=gs://bucket/file.csv ds.table`
* Б) `gcloud storage cp gs://bucket/file.csv bq://ds.table`
* В) `bq query --destination_table=ds.table 'SELECT * FROM gs://bucket/file.csv'`
* Г) `bq load --source_format=CSV --skip_leading_rows=1 --autodetect ds.table gs://bucket/file.csv` ✅

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). `bq load` с `--autodetect` и `--skip_leading_rows=1` загружает CSV и выводит схему. `bq mk --external_table_definition` создаёт внешнюю таблицу, а не загружает данные; `gcloud storage cp` не пишет в BigQuery; SQL не читает gs:// напрямую.

Вопрос 57 🟨 применение · средний
A retailer needs a relational database for global inventory. Writes come from three continents, transactions must be strongly consistent across regions, and the database must scale horizontally with 99.999% availability. Which service should you use?

---

* А) Cloud SQL for PostgreSQL with cross-region read replicas
* Б) Spanner with a multi-region configuration ✅
* В) Bigtable with replication
* Г) Firestore in Datastore mode

Тема: S1 Data preparation and ingestion

Разбор: S1 (1.2). Spanner — реляционная база с глобальной строгой согласованностью, горизонтальным масштабированием и SLA 99,999% в multi-region. Реплики Cloud SQL только для чтения; Bigtable и Firestore не реляционные и не дают глобальных SQL-транзакций.

Вопрос 58 🟨 применение · средний
Your team trains BigQuery ML models and wants to manage their versions and deploy them to online endpoints alongside other ML models. What should you do?

---

* А) Export each model to Cloud Storage and track versions in a spreadsheet
* Б) Copy the models to a separate dataset for each version
* В) Store model metadata in Firestore
* Г) Register the models in Vertex AI Model Registry with `model_registry = 'VERTEX_AI'` in `CREATE MODEL` ✅

Тема: S2 Data analysis and presentation

Разбор: S2 (2.3). Опция `model_registry='VERTEX_AI'` (с `vertex_ai_model_id`) регистрирует модель BQML в Vertex AI Model Registry: версии, алиасы, деплой на endpoint. Остальное — ручной учёт без деплоя.

Вопрос 59 🟨 применение · средний
Every night you run three dependent Spark jobs. To save costs, the cluster must exist only while the jobs run. You want a Dataproc-native solution with the least operational effort. What should you do?

---

* А) Keep a long-running Dataproc cluster and submit jobs with cron
* Б) Create a Dataproc Workflow Template with a managed cluster and instantiate it on a schedule ✅
* В) Run the jobs on a Compute Engine VM with Spark installed
* Г) Use BigQuery scheduled queries to start the Spark jobs

Тема: S3 Data pipeline orchestration

Разбор: S3 (3.2). Workflow Template с managed cluster создаёт кластер, выполняет задания по графу зависимостей и удаляет кластер. Постоянный кластер платный и днём, VM — ручное администрирование, scheduled queries не запускают Spark.

Вопрос 60 🟨 применение · средний
A security reviewer asks how data is protected in Google Cloud. Which two statements are true? (Choose two.)

---

* ☑ ✅ Data at rest is encrypted by default with Google-managed keys
* ☐ CMEK must be configured before any data is encrypted at rest
* ☑ ✅ Data in transit between users and Google front ends is encrypted with TLS
* ☐ Encryption at rest also protects data while it travels over the network
* ☐ CSEK is the default encryption method for BigQuery tables

Тема: S4 Data management

Разбор: S4 (4.4). По умолчанию все данные в покое шифруются ключами Google (GMEK), трафик к Google Front End защищён TLS. CMEK опционален, шифрование at rest не защищает передачу по сети, CSEK — не значение по умолчанию и не поддерживается в BigQuery.

---

Ответы: 1 — Г · 2 — В · 3 — 1, 3 · 4 — А · 5 — Б · 6 — 2, 4 · 7 — А · 8 — В · 9 — 1, 3 · 10 — А · 11 — Б · 12 — Г · 13 — Б · 14 — В · 15 — А · 16 — Б · 17 — Г · 18 — Г · 19 — Г · 20 — Б · 21 — А · 22 — Б · 23 — В · 24 — В · 25 — А · 26 — В · 27 — Б · 28 — В · 29 — Б · 30 — А · 31 — А · 32 — 1, 4 · 33 — В · 34 — Г · 35 — Б · 36 — А · 37 — Б · 38 — В · 39 — Б · 40 — Б · 41 — Г · 42 — 2, 4 · 43 — В · 44 — Г · 45 — А · 46 — Б · 47 — А · 48 — В · 49 — В · 50 — Б · 51 — Б · 52 — Б · 53 — Г · 54 — А · 55 — 1, 3 · 56 — Г · 57 — Б · 58 — Г · 59 — Б · 60 — 1, 3
