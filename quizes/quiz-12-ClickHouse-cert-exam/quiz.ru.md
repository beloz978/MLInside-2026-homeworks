---
audience: "Data engineers, готовящиеся к ClickHouse Certified Developer"
purpose: "Один пробный экзамен в объёме и сложности настоящего: 12 заданий по 5 официальным областям, формулировки на английском, разбор на русском"
goal: "Выбирать правильное решение в ClickHouse: ключ сортировки и типы, загрузка файлов, аналитические запросы, materialized views, индексы и проекции, дедупликация и мутации"
context: "Официальные цели экзамена (5 областей, 19 целей) из проекта MyCerts; каждое решение и каждая «ловушка» проверены на ClickHouse 26.11; контекст сессии — в каталоге session/"
prerequisites: "Базовый SQL; clickhouse-client; семейство MergeTree"
duration_min: 120
---

Тест 12. ClickHouse Certified Developer — пробный экзамен

Настоящий экзамен — практический: 10–12 заданий в `clickhouse-client` за 2 часа, порог 70%, документация открыта, ИИ запрещён. Здесь те же объём и время в формате выбора решения: 12 вопросов на английском, разбор на русском. Распределение по областям: Modeling — 2, Inserting — 2, Analyzing — 2, Optimizing — 3, Dedup and mutations — 3. Уровни: 🟩 понимание — 2, 🟨 применение — 7, 🟥 анализ — 3. Сложность: простой — 3, средний — 6, сложный — 3. Во всех вопросах один верный ответ. Режим по умолчанию — `exam`: без подсказок, варианты перемешаны, разбор и промпты только в конце; на весь тест — 120 минут, порог зачёта — 70% (9 из 12).

---

Вопрос 1 🟨 применение · простой
Тема: Моделирование
You are creating a table for 5 billion billing events. Queries almost always filter by `tenant_id` (about 300 distinct values) and by a time range, and `price` must be stored exactly. Which table definition should you use?

---

* А) `CREATE TABLE ev (tenant_id UInt32, ts DateTime, country LowCardinality(String), price Float64) ENGINE = MergeTree ORDER BY (ts, tenant_id)`
* Б) `CREATE TABLE ev (tenant_id UInt32, ts String, country String, price Float64) ENGINE = MergeTree ORDER BY tenant_id`
* В) `CREATE TABLE ev (tenant_id UInt32, ts DateTime, country LowCardinality(String), price Decimal(12, 2)) ENGINE = MergeTree ORDER BY (tenant_id, ts)` ✅
* Г) `CREATE TABLE ev (tenant_id Nullable(UInt32), ts DateTime, country String, price Decimal(12, 2)) ENGINE = MergeTree ORDER BY (tenant_id, ts)`

Разбор: D1 Modeling (1.1–1.3). Ключ сортировки строится по фильтрам: сначала колонка с малой кардинальностью (`tenant_id`), затем время — тогда диапазон по времени внутри арендатора читается одним куском гранул. `ORDER BY (ts, tenant_id)` ставит самую «широкую» колонку первой, и фильтр по `tenant_id` почти не отсекает гранулы. Деньги хранят в `Decimal`, а не в `Float64` (погрешность). Время — `DateTime`, не `String`. `Nullable` в ключе по умолчанию запрещён (нужна настройка `allow_nullable_key`) и замедляет запросы. `LowCardinality(String)` — удачный тип для колонки с небольшим числом значений.

Вопрос 2 🟨 применение · средний
Тема: Моделирование
Table `orders` has `country_id UInt64`. The small table `countries (id UInt64, name String)` changes rarely. You created: `CREATE DICTIONARY dict_country (id UInt64, name String) PRIMARY KEY id SOURCE(CLICKHOUSE(TABLE 'countries')) LAYOUT(FLAT()) LIFETIME(300)`. Which query returns the country name for every order without a JOIN?

---

* А) `SELECT order_id, dictGet('dict_country', country_id, 'name') FROM orders`
* Б) `SELECT order_id, dictGet('dict_country', 'name', country_id) FROM orders` ✅
* В) `SELECT order_id, dictGet(dict_country, name, country_id) FROM orders`
* Г) `SELECT order_id, joinGet('dict_country', 'name', country_id) FROM orders`

Подсказка: Имя словаря и имя атрибута — строковые литералы, а ключ идёт последним аргументом.

Разбор: D1 Modeling (1.4). Сигнатура — `dictGet('словарь', 'атрибут', ключ)`. Перестановка аргументов (А) даёт `Code 43 ILLEGAL_TYPE_OF_ARGUMENT`, имена без кавычек (В) — `Code 47 UNKNOWN_IDENTIFIER`, `joinGet` (Г) работает только с таблицами движка Join (`Code 43: Table dict_country should have engine StorageJoin`). Проверено на 26.11. Документация: `sql-reference/functions/ext-dict-functions`, `sql-reference/dictionaries`.

Вопрос 3 🟩 понимание · простой
Тема: Загрузка данных
The file `/home/me/events.csv` (with a header row) is on the machine where you run `clickhouse-client`; the server is remote. You need to load it into the table `events`. Which statement should you use?

---

* А) `INSERT INTO events FROM INFILE '/home/me/events.csv' FORMAT CSVWithNames` ✅
* Б) `INSERT INTO events SELECT * FROM file('/home/me/events.csv', CSVWithNames)`
* В) `COPY events FROM '/home/me/events.csv' WITH (FORMAT csv, HEADER true)`
* Г) `LOAD DATA LOCAL INFILE '/home/me/events.csv' INTO TABLE events`

Разбор: D2 Inserting (2.1). `INSERT … FROM INFILE` читает файл на стороне клиента и отправляет данные серверу; формат задаётся словом `FORMAT` в конце. Табличная функция `file()` читает файлы сервера из `user_files_path`, а не файлы клиента. `COPY … FROM` (PostgreSQL) и `LOAD DATA` (MySQL) в ClickHouse не существуют. Для подтверждения после загрузки выполните `SELECT count()`.

Вопрос 4 🟨 применение · средний
Тема: Загрузка данных
The table `events (ts DateTime, user_id UInt64, url String, domain String)` is empty. A CSV file with a header, available at `https://example.com/events.csv`, has the columns `ts_unix` (Unix seconds), `user_id` and `url`. The column `domain` must contain the host name of `url`. Which statement loads the data correctly?

---

* А) `INSERT INTO events SELECT * FROM url('https://example.com/events.csv', 'CSVWithNames')`
* Б) `INSERT INTO events SELECT toDateTime(ts_unix), user_id, url, domain(url) FROM url('https://example.com/events.csv', 'CSVWithNames')` ✅
* В) `INSERT INTO events (ts, user_id, url) SELECT * FROM url('https://example.com/events.csv', 'CSVWithNames')`
* Г) `INSERT INTO events SELECT toDateTime(ts_unix), user_id, url FROM url('https://example.com/events.csv', 'CSVWithNames')`

Подсказка: Число и порядок колонок в `SELECT` должны совпадать с таблицей, а `domain()` извлекает хост из URL.

Разбор: D2 Inserting (2.2–2.3). Преобразования при вставке делаются в `INSERT … SELECT`: колонки перечисляются в порядке таблицы, значения считаются выражениями. Вариант Г падает с `Code 20 NUMBER_OF_COLUMNS_DOESNT_MATCH` (3 колонки против 4). Варианты А и В не падают, но молча дают неверные данные: `ts` остаётся `1970-01-01 00:00:00`, а `domain` пустой (проверено на 26.11 с `file()`). Это худший класс ошибок на практическом экзамене — вставка прошла, данные неверны, поэтому после загрузки всегда проверяйте `SELECT * … LIMIT 3`.

Вопрос 5 🟨 применение · средний
Тема: Анализ данных
Table `requests (ts DateTime, endpoint String, user_id UInt64, latency_ms UInt32)`. Return the 10 endpoints with the highest 95th percentile of latency over the last 24 hours, together with the number of distinct users. Approximate results are acceptable. Which query is correct?

---

* А) `SELECT endpoint, quantile(latency_ms, 0.95) AS p95, uniq(user_id) AS users FROM requests WHERE ts >= now() - INTERVAL 1 DAY GROUP BY endpoint ORDER BY p95 DESC LIMIT 10`
* Б) `SELECT endpoint, percentile(latency_ms, 95) AS p95, uniq(user_id) AS users FROM requests WHERE ts >= now() - INTERVAL 1 DAY GROUP BY endpoint ORDER BY p95 DESC LIMIT 10`
* В) `SELECT endpoint, quantile(0.95)(latency_ms) AS p95, uniq(user_id) AS users FROM requests WHERE ts >= now() - INTERVAL 1 DAY GROUP BY endpoint ORDER BY users DESC LIMIT 10`
* Г) `SELECT endpoint, quantile(0.95)(latency_ms) AS p95, uniq(user_id) AS users FROM requests WHERE ts >= now() - INTERVAL 1 DAY GROUP BY endpoint ORDER BY p95 DESC LIMIT 10` ✅

Подсказка: Уровень квантиля у параметрических агрегатных функций ClickHouse записывается в первых скобках.

Разбор: D3 Analyzing (3.2–3.3). Правильный синтаксис — `quantile(0.95)(col)`: уровень в первых скобках, столбец во вторых. `quantile(col, 0.95)` даёт `Code 42 NUMBER_OF_ARGUMENTS_DOESNT_MATCH`, функции `percentile` в ClickHouse нет (`Code 46 UNKNOWN_FUNCTION`). Вариант В сортирует по `users`, а не по p95. `quantile` и `uniq` — приближённые функции; если нужна точность, берут `quantileExact` и `uniqExact`. Проверено на 26.11.

Вопрос 6 🟩 понимание · простой
Тема: Анализ данных
Table `events (ts DateTime, url String)`. Count events per 15-minute bucket, only for rows whose `url` contains the word `checkout` in any letter case. Which query is correct?

---

* А) `SELECT toStartOfInterval(ts, INTERVAL 15 MINUTE) AS b, count() FROM events WHERE url ILIKE '%checkout%' GROUP BY b ORDER BY b` ✅
* Б) `SELECT toStartOfHour(ts) AS b, count() FROM events WHERE url ILIKE '%checkout%' GROUP BY b ORDER BY b`
* В) `SELECT toStartOfInterval(ts, INTERVAL 15 MINUTE) AS b, count() FROM events WHERE url LIKE '%checkout%' GROUP BY b ORDER BY b`
* Г) `SELECT toStartOfInterval(ts, INTERVAL 15 MINUTE) AS b, count() FROM events WHERE position(url, 'checkout') > 0 GROUP BY b ORDER BY b`

Разбор: D3 Analyzing (3.1, 3.4). `toStartOfInterval(ts, INTERVAL 15 MINUTE)` — универсальный способ получить корзину времени, а `ILIKE` и `positionCaseInsensitive` ищут подстроку без учёта регистра. `LIKE` и `position` различают регистр, поэтому в тестовых данных с `/Checkout/` они возвращают 0 строк, а `ILIKE` — все 5000 (проверено на 26.11). `toStartOfHour` даёт корзины по часу, а не по 15 минут.

Вопрос 7 🟨 применение · средний
Тема: Оптимизация
Table `events` already contains 2 billion rows. You created `events_by_day (day Date, n UInt64) ENGINE = SummingMergeTree ORDER BY day` and `CREATE MATERIALIZED VIEW events_by_day_mv TO events_by_day AS SELECT toDate(ts) AS day, count() AS n FROM events GROUP BY day`. The target table must contain counts for all existing and future rows. What should you do?

---

* А) Do nothing: a materialized view also processes the rows that were inserted into `events` before the view was created
* Б) Run `OPTIMIZE TABLE events_by_day FINAL` so that the old rows are merged into the target
* В) Run `INSERT INTO events_by_day SELECT toDate(ts), count() FROM events WHERE ts < '<view creation time>' GROUP BY 1` ✅
* Г) Run `SYSTEM REFRESH VIEW events_by_day_mv` to rebuild the view from the source table

Подсказка: Materialized view — это триггер на вставку: он видит только блоки, вставленные после его создания.

Разбор: D4 Optimizing (4.1–4.2). Обычная materialized view с `TO` обрабатывает только новые вставки, поэтому историю нужно досыпать вручную запросом `INSERT … SELECT` с тем же `SELECT`, ограничив его моментом создания view (иначе строки посчитаются дважды). Проверено: после создания view и одной вставки в целевой таблице оказалась 1 строка, а не вся история. `OPTIMIZE` только сливает уже существующие куски, а `SYSTEM REFRESH VIEW` относится к refreshable MV (`REFRESH EVERY …`), а не к обычным.

Вопрос 8 🟥 анализ · сложный
Тема: Оптимизация
You need daily unique users and total revenue from `events (ts DateTime, user_id UInt64, amount UInt64)`; dashboards read hundreds of billions of rows. Which design is correct (target table / materialized view / dashboard query)?

---

* А) SummingMergeTree `(day, users UInt64, revenue UInt64)` / `uniq(user_id) AS users, sum(amount) AS revenue … GROUP BY day` / `SELECT day, sum(users), sum(revenue) FROM t GROUP BY day`
* Б) AggregatingMergeTree `(day, users AggregateFunction(uniq, UInt64), revenue SimpleAggregateFunction(sum, UInt64))` / `uniqState(user_id) AS users, sum(amount) AS revenue … GROUP BY day` / `SELECT day, uniqMerge(users), sum(revenue) FROM t GROUP BY day` ✅
* В) AggregatingMergeTree `(day, users AggregateFunction(uniq, UInt64), revenue SimpleAggregateFunction(sum, UInt64))` / `uniq(user_id) AS users, sum(amount) AS revenue … GROUP BY day` / `SELECT day, uniqMerge(users), sum(revenue) FROM t GROUP BY day`
* Г) AggregatingMergeTree `(day, users AggregateFunction(uniq, UInt64), revenue SimpleAggregateFunction(sum, UInt64))` / `uniqState(user_id) AS users, sum(amount) AS revenue … GROUP BY day` / `SELECT day, uniq(users), sum(revenue) FROM t GROUP BY day`

Подсказка: Уникальных пользователей нельзя складывать между частями: нужно хранить промежуточное состояние агрегата.

Подсказка: Запись состояния — суффикс `-State`, чтение и слияние — `-Merge`.

Разбор: D4 Optimizing (4.2). Для неаддитивных агрегатов (`uniq`, квантили) хранят состояние: тип `AggregateFunction(uniq, UInt64)`, запись `uniqState`, чтение `uniqMerge`. А даёт завышенные числа: сумма уникальных по частям — не число уникальных. В падает при создании view с `Code 70 CANNOT_CONVERT_TYPE` (нельзя записать UInt64 в колонку состояния). Г не падает, но молча возвращает неверный результат: на тестовых данных вместо 7 уникальных пользователей он вернул 1 (проверено на 26.11). Аддитивный `revenue` удобно хранить как `SimpleAggregateFunction(sum, UInt64)`.

Вопрос 9 🟨 применение · средний
Тема: Оптимизация
Table `events` has `ORDER BY ts`. Dashboards run `WHERE user_id = 42` and read almost every granule, although the values of `user_id` are stored in clusters (each user appears in a narrow time window). The data already in the table must also benefit. What should you do?

---

* А) `ALTER TABLE events ADD INDEX idx_user user_id TYPE set(100) GRANULARITY 1`
* Б) `ALTER TABLE events MODIFY ORDER BY user_id`
* В) `ALTER TABLE events ADD INDEX idx_user user_id TYPE set(100) GRANULARITY 1`, then `ALTER TABLE events MATERIALIZE PROJECTION idx_user`
* Г) `ALTER TABLE events ADD INDEX idx_user user_id TYPE set(100) GRANULARITY 1`, then `ALTER TABLE events MATERIALIZE INDEX idx_user` ✅

Подсказка: Индекс пропуска, добавленный через `ALTER`, применяется только к новым кускам, пока его не построят для старых.

Подсказка: Результат проверяется командой `EXPLAIN indexes = 1`.

Разбор: D4 Optimizing (4.4). Skip-индекс (`set`, `minmax`, `bloom_filter`) после `ADD INDEX` строится лишь для новых кусков; для существующих нужен `MATERIALIZE INDEX`. Проверено на 26.11: до материализации `EXPLAIN indexes = 1` показывает `Granules: 24/24`, после — `1/24`. `MODIFY ORDER BY` может только дописать новые колонки в конец ключа и не позволяет заменить ключ (`Code 36 BAD_ARGUMENTS`). `MATERIALIZE PROJECTION` относится к проекциям и для индекса не работает. Индекс полезен именно потому, что значения коррелируют с порядком хранения: при случайном `user_id` set-индекс почти ничего не отсекает.

Вопрос 10 🟥 анализ · сложный
Тема: Дедупликация и мутации
`DELETE FROM events WHERE user_id = 42` fails with `Code 344 SUPPORT_IS_DISABLED` because `events` has a projection. You must keep the projection and use the lightweight `DELETE` statement. What should you do?

---

* А) Run `ALTER TABLE events MODIFY SETTING lightweight_mutation_projection_mode = 'rebuild'`, then repeat the `DELETE` ✅
* Б) Append `SETTINGS lightweight_mutation_projection_mode = 'rebuild'` to the `DELETE` statement itself and run it again
* В) Run `OPTIMIZE TABLE events FINAL`, then repeat the `DELETE`
* Г) Run `ALTER TABLE events DROP PROJECTION …`, then repeat the `DELETE` and recreate the projection afterwards

Подсказка: Режим работы лёгкого удаления с проекциями — это настройка таблицы, а не запроса.

Разбор: D5 Dedup and mutations (5.1) × D4 (4.3). По умолчанию `lightweight_mutation_projection_mode = 'throw'`, и `DELETE` на таблице с проекциями отклоняется. Решение — сменить режим в настройках таблицы (`rebuild` пересобирает проекции, `drop` удаляет их из затронутых кусков). Проверено на 26.11: `SETTINGS` в самом `DELETE` ошибку не снимает (тот же Code 344), а после `ALTER … MODIFY SETTING` удаление проходит. Вариант Г нарушает условие «сохранить проекцию», а `OPTIMIZE` на режим не влияет.

Вопрос 11 🟨 применение · средний
Тема: Дедупликация и мутации
Table `users` receives a new row with the current `updated_at` on every profile change. Queries must return only the latest row per `id` immediately, without waiting for background merges. Which definition and query do this?

---

* А) `ENGINE = ReplacingMergeTree ORDER BY (id, updated_at)`, query `SELECT * FROM users`
* Б) `ENGINE = ReplacingMergeTree(updated_at) ORDER BY id`, query `SELECT * FROM users`
* В) `ENGINE = ReplacingMergeTree(updated_at) ORDER BY id`, query `SELECT * FROM users FINAL` ✅
* Г) `ENGINE = ReplacingMergeTree(id) ORDER BY updated_at`, query `SELECT * FROM users FINAL`

Подсказка: Дубликаты определяются по ключу сортировки, а выбор победителя — по колонке версии.

Разбор: D5 Dedup and mutations (5.2). `ReplacingMergeTree(ver)` оставляет при слиянии строку с наибольшей версией среди строк с одинаковым ключом сортировки, но слияния асинхронны, поэтому до них нужен `FINAL`. В варианте А `updated_at` входит в ключ, и строки с разным временем не считаются дубликатами (проверено: `FINAL` вернул обе строки). В Б без `FINAL` запрос видит обе версии (проверено). В Г ключ и версия перепутаны местами. `FINAL` удобно сочетать с `WHERE` по колонкам ключа, чтобы не читать лишнее.

Вопрос 12 🟥 анализ · сложный
Тема: Дедупликация и мутации
Table `balances (id UInt64, v UInt32, sign Int8)` uses `CollapsingMergeTree(sign) ORDER BY id` and contains the row `(1, 10, 1)`. You must change `v` to 20 so that `SELECT id, sum(v * sign) FROM balances GROUP BY id` returns 20. Which `INSERT` do you run?

---

* А) `INSERT INTO balances VALUES (1, 20, 1)`
* Б) `INSERT INTO balances VALUES (1, 10, -1), (1, 20, 1)` ✅
* В) `INSERT INTO balances VALUES (1, 20, -1)`
* Г) `INSERT INTO balances VALUES (1, 10, 1), (1, 20, -1)`

Подсказка: Строка отмены должна повторять старое состояние со знаком −1, затем идёт новое состояние со знаком +1.

Подсказка: Проверьте суммы: 10 − 10 + 20.

Разбор: D5 Dedup and mutations (5.3). В `CollapsingMergeTree` «обновление» — это пара строк: отмена старого состояния (те же значения, `sign = -1`) и новое состояние (`sign = 1`). Тогда `sum(v * sign) = 10 − 10 + 20 = 20` и до, и после слияний; для строк «как есть» используют `FINAL`. Остальные варианты дают А: 30, В: −10, Г: 0 (в Г знаки перевёрнуты, и `FINAL` показал бы устаревшее `(1, 10, 1)`). Проверено на 26.11. Если отмена и состояние могут прийти в разных пакетах не по порядку, `FINAL` на `CollapsingMergeTree` ведёт себя неверно, и надёжнее `VersionedCollapsingMergeTree`.

---

Ответы: 1 — В · 2 — Б · 3 — А · 4 — Б · 5 — Г · 6 — А · 7 — В · 8 — Б · 9 — Г · 10 — А · 11 — В · 12 — Б

Резерв 1 🟩 понимание · простой
Тема: Моделирование
Which statement about the primary key of a MergeTree table is correct?

---

* А) It guarantees that no two rows have the same key value
* Б) It is a dense index with one entry for every row
* В) It must always be different from the `ORDER BY` expression
* Г) It is a sparse index with one entry per granule (8192 rows by default) ✅

Разбор: D1 Modeling (1.3). Первичный ключ MergeTree — разреженный индекс: одна запись на гранулу (по умолчанию 8192 строки), он ускоряет чтение, но не обеспечивает уникальность. Если `PRIMARY KEY` не задан, он совпадает с `ORDER BY`; если задан, он обязан быть префиксом ключа сортировки.

Резерв 2 🟨 применение · средний
Тема: Загрузка данных
A gzip-compressed TSV file `events.tsv.gz` is on the machine where you run `clickhouse-client`. Which statement loads it into `t`?

---

* А) `INSERT INTO t FROM INFILE 'events.tsv.gz' COMPRESSION 'gzip' FORMAT TabSeparated` ✅
* Б) `INSERT INTO t FORMAT TabSeparated FROM INFILE 'events.tsv.gz'`
* В) `INSERT INTO t FROM INFILE 'events.tsv.gz' FORMAT TabSeparated GZIP`
* Г) `INSERT INTO t SELECT * FROM INFILE('events.tsv.gz', 'TabSeparated')`

Подсказка: В `INSERT … FROM INFILE` сначала идёт файл, затем сжатие и формат.

Разбор: D2 Inserting (2.1, 2.3). Порядок частей: `FROM INFILE файл [COMPRESSION тип] [SETTINGS …] [FORMAT формат]`. В Б после `FORMAT TabSeparated` клиент ждёт данные и пытается разобрать текст `FROM INFILE …` как строку таблицы (`Code 27 CANNOT_PARSE_INPUT_ASSERTION_FAILED`, проверено). Табличной функции `INFILE()` нет.

Резерв 3 🟨 применение · средний
Тема: Анализ данных
Table `sales (cat String, item String, n UInt32)`. Return the 3 best-selling items (by `n`) in each category. Which query is correct?

---

* А) `SELECT cat, item, n FROM sales ORDER BY n DESC LIMIT 3 GROUP BY cat`
* Б) `SELECT cat, item, n FROM sales ORDER BY cat, n DESC LIMIT 3`
* В) `SELECT cat, item, n FROM sales ORDER BY cat, n DESC LIMIT 3 BY cat` ✅
* Г) `SELECT cat, item, n FROM sales WHERE row_number() <= 3 PARTITION BY cat`

Подсказка: В ClickHouse есть отдельная конструкция «первые N строк в каждой группе».

Разбор: D3 Analyzing (3.2). `LIMIT n BY колонка` оставляет первые n строк для каждого значения колонки после сортировки (проверено: по 2 лучших строки в каждой категории). Обычный `LIMIT 3` ограничивает весь результат; `LIMIT … GROUP BY` и `WHERE row_number()` — несуществующий синтаксис.

Резерв 4 🟨 применение · средний
Тема: Оптимизация
You added the projection `by_user (SELECT user_id, sum(v) GROUP BY user_id)` to table `p`. How do you verify that the query `SELECT user_id, sum(v) FROM p GROUP BY user_id` reads from the projection?

---

* А) `SELECT * FROM system.projections WHERE name = 'by_user'`
* Б) `EXPLAIN indexes = 1 SELECT user_id, sum(v) FROM p GROUP BY user_id` and look for `ReadFromMergeTree (by_user)` ✅
* В) `DESCRIBE TABLE p`
* Г) `CHECK TABLE p`

Подсказка: Нужен план конкретного запроса, а не описание таблицы.

Разбор: D4 Optimizing (4.3). Только `EXPLAIN` показывает, что оптимизатор выбрал проекцию: в плане источник называется `ReadFromMergeTree (by_user)` вместо `ReadFromMergeTree (default.p)` (проверено на 26.11). `system.projections` лишь подтверждает, что проекция существует, а `DESCRIBE` и `CHECK TABLE` вообще не касаются плана.

Резерв 5 🟨 применение · средний
Тема: Оптимизация
Table `sm` is `SummingMergeTree ORDER BY day` with columns `(day Date, n UInt64)`. Two separate inserts put `('2026-10-01', 1)` and `('2026-10-01', 2)` into it. Which query is guaranteed to return 3 for that day at any moment?

---

* А) `SELECT day, n FROM sm`
* Б) `SELECT day, any(n) FROM sm GROUP BY day`
* В) `SELECT day, n FROM sm ORDER BY day LIMIT 1 BY day`
* Г) `SELECT day, sum(n) FROM sm GROUP BY day` ✅

Подсказка: Строки суммируются лишь при фоновых слияниях.

Разбор: D4 Optimizing (4.2). `SummingMergeTree` суммирует строки с одинаковым ключом только при слиянии, поэтому до него в таблице лежат обе строки (проверено: `SELECT * FROM sm` вернул 2 и 1). Корректный запрос всегда повторяет `sum()` и `GROUP BY`. Остальные варианты возвращают произвольную из строк.

Резерв 6 🟥 анализ · сложный
Тема: Дедупликация и мутации
You need `ReplacingMergeTree` with the version column `updated_at DateTime` and the delete flag `is_deleted UInt8`. Which engine definition is correct?

---

* А) `ReplacingMergeTree(updated_at, is_deleted)` ✅
* Б) `ReplacingMergeTree(is_deleted, updated_at)`
* В) `ReplacingMergeTree(is_deleted)`
* Г) `ReplacingMergeTree(updated_at) PARTITION BY is_deleted`

Подсказка: Версия идёт первым аргументом, флаг удаления — вторым; флаг без версии не работает.

Разбор: D5 Dedup and mutations (5.2). Сигнатура — `ReplacingMergeTree([ver [, is_deleted]])`. Если указать только `is_deleted` (В), движок молча воспримет колонку как версию — создание таблицы проходит без ошибки (проверено), но флаг удаления не действует. При перестановке аргументов (Б) создание падает (`Code 169 BAD_TYPE_OF_FIELD: is_deleted column (updated_at) … must have type UInt8`). При правильной записи `FINAL` скрывает ключи, у которых последняя версия помечена удалённой (проверено: 0 строк). `PARTITION BY` дубликаты не убирает.

---

Ответы резерва: 1 — Г · 2 — А · 3 — В · 4 — Б · 5 — Г · 6 — А
