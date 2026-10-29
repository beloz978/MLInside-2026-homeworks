# Введение в dbt. Домашнее задание (Olist)

## Задание

Возьмите датасет **Olist** — публичные данные бразильского маркетплейса ([Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)): 9 таблиц, ~100 тыс. заказов за 2016–2018 годы — и реализуйте на его основе проект dbt.

---

## 0) Исходные данные: загрузите сами через `kagglehub` и `dbt seed`

Данные на Kaggle общедоступны, токен не нужен. Скачайте датасет и положите CSV в каталог `seeds/` вашего dbt-проекта:

```python
import kagglehub

path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")   # каталог с 9 CSV
# скопируйте нужные CSV из path в <ваш-проект>/seeds/
```

Затем загрузите их в хранилище командой `dbt seed` — **до** `dbt build`: модели обращаются к данным через `source()`, и dbt не знает, что их создаёт seed, поэтому сам порядок не выстроит. Нужны 8 таблиц, огромная `olist_geolocation_dataset` не требуется. Файлы из `seeds/` в git не коммитьте (добавьте `seeds/*.csv` в `.gitignore`): в PR идёт только код, а данные каждый скачивает сам.

**Если данные уже загружены в предыдущих заданиях** (например, в ClickHouse после ДЗ по Kafka и ClickHouse), можно использовать их: опишите их в `sources.yml`, а недостающие таблицы догрузите через `dbt seed`.

Автопроверка сверяет **полноту** исходных данных: все 8 таблиц на месте, число строк, ключевые колонки и контрольные суммы. Ожидаемые значения:

| Таблица (CSV) | Строк |
|---|---|
| `olist_orders_dataset` | 99 441 |
| `olist_order_items_dataset` | 112 650 |
| `olist_customers_dataset` | 99 441 |
| `olist_products_dataset` | 32 951 |
| `olist_sellers_dataset` | 3 095 |
| `olist_order_payments_dataset` | 103 886 |
| `olist_order_reviews_dataset` | 99 224 |
| `product_category_name_translation` | 71 |

Если число строк не сходится, чаще всего CSV скопирован не целиком или `dbt seed` прервался: перезапустите `dbt seed --full-refresh`.

---

## 1) Модель данных: от raw до витрин

Создайте слоистую архитектуру моделей: raw (source, данные из шага 0) → staging → marts (если хотите, то слоёв мб больше).

### Staging-слой
- Очистка и нормализация сырых данных, приведение типов, добавление вычисляемых полей (например, сегментация суммы через макрос, признак опоздания доставки)

### Витрины (marts)

Реализуйте следующие аналитические витрины (все не обязательно – от количества реализованных зависит оценка – см в самом конце таблицу оценок):

#### 1. `mart_daily_state_metrics` — Дневные метрики по штатам
- Агрегация заказов по дате и штату клиента
- Метрики: количество заказов, сумма, средний чек, P95, доля крупных заказов

#### 2. `mart_delivery_by_state` — Географический анализ доставки
- Распределение опозданий доставки по штатам Бразилии
- Метрики: late_rate (%), средний срок доставки и задержки, уникальные клиенты/продавцы

#### 3. `mart_category_performance` — Анализ по категориям товаров
- Выявление категорий с наибольшей выручкой и наибольшей долей проблемных заказов
- Метрики: число заказов, выручка, средняя цена, средняя оценка, late_rate (%)

#### 4. `mart_customer_profile` — Профиль клиентов
- Сегментация клиентов по ценности (HIGH/MEDIUM/LOW)
- История заказов, сумма покупок, средний чек, давность последнего заказа

#### 5. `mart_hourly_order_pattern` — Временные паттерны спроса
- Анализ по дням недели и часам
- Выявление временных окон с повышенным спросом

#### 6. `mart_seller_analytics` — Аналитика по продавцам
- Метрики по каждому продавцу: оборот, средняя оценка, late_rate, флаг проблемного продавца

### Контракт колонок витрин

Имена колонок фиксированы: по ним автопроверка сверяет цифры с эталоном (допускаются дополнительные колонки). Определения метрик:

- **заказ** — заказ, у которого есть хотя бы одна позиция (`order_items`); сумма заказа — `sum(price)` его позиций, **без** `freight_value`;
- **GMV** — `sum(price)`; сумма в витринах должна сходиться с ней (платежи и отзывы не должны размножать строки);
- **опоздание** (`late`) — заказ в статусе `delivered`, дата доставки известна и строго позже обещанной;
- **день недели** — ISO, `1` = понедельник; время — по `order_purchase_timestamp`;
- **крупный заказ** — сумма заказа >= 200; `recency_days` считается от максимальной даты покупки в данных, а не от `now()`.

| Витрина | Зерно | Обязательные колонки |
|---|---|---|
| `mart_daily_state_metrics` | order_date × customer_state | `order_date`, `customer_state`, `orders_cnt`, `gmv`, `avg_order_value`, `p95_order_value`, `large_orders_share` |
| `mart_delivery_by_state` | customer_state (только доставленные с известной датой) | `customer_state`, `delivered_orders`, `late_orders`, `late_rate_pct`, `avg_delivery_days`, `unique_customers`, `unique_sellers` |
| `mart_category_performance` | product_category | `product_category`, `orders_cnt`, `revenue`, `avg_price`, `avg_review_score`, `late_rate_pct` |
| `mart_customer_profile` | customer_unique_id | `customer_unique_id`, `orders_cnt`, `total_spent`, `avg_order_value`, `recency_days`, `segment` |
| `mart_hourly_order_pattern` | day_of_week (ISO, 1=пн) × hour_of_day (0–23) | `day_of_week`, `hour_of_day`, `orders_cnt` |
| `mart_seller_analytics` | seller_id | `seller_id`, `orders_cnt`, `revenue`, `avg_review_score`, `late_rate_pct`, `is_problem_seller` |

---

## 2) Описания, тесты и макросы

### Макросы
- Создайте минимум 1 собственный макрос
- Используйте макрос в staging или mart моделях

### Метаданные (schema.yml)
- Опишите все модели и ключевые колонки
- Добавьте descriptions для бизнес-контекста

### Тесты
- Базовые: `not_null`, `unique`, `accepted_values`, `relationships`
- На витрины: проверка уникальности комбинаций ключей
- Singular tests (кастомные SQL-тесты в папке `tests/`) — количество зависит от оценки

---

## 3) Документация

Сгенерируйте dbt Docs и приложите скриншот DAG или страницы документации.

---

## 4) Дополнительные артефакты (по желаемой оценке)

### На 6-7 баллов:
- ✅ Исходные данные загружены полностью (`kagglehub` + `dbt seed`, или готовые таблицы + недостающее через seed)
- ✅ 2 витрины
- ✅ Создать и использовать свой макрос
- ✅ Использовать стандартные пакеты: `dbt_utils`, `dbt_date`
- ✅ `schema.yml` с описанием метаданных и тестами
- ✅ 1 singular test

### На 8-9 баллов:
Всё из 6-7, плюс:
- ✅ 4 витрины
- ✅ 3–5 singular tests
- ✅ 1–3 unit tests (dbt 1.8+)
- ✅ Минимум 2 пакета для QA данных из: `audit_helper`, `dbt_expectations`, `elementary`, `dbt_meta_testing`, `dbt_profiler`
- ✅ `.pre-commit-config.yaml`:
  - `sqlfluff` для линтинга SQL
  - проверка, что проект собирается (`dbt parse`)
  - минимум 1 хук проверки dbt-проекта: `dbt-checkpoint`, `dbt-score`, `dbt-bouncer` или `dbt-coverage`
- ✅ `Makefile` или `justfile`

> Часть пакетов может не поддерживать ваш адаптер. Если пакет не заработал — выберите другой из списка и коротко напишите об этом в PR.

### На 10 баллов:
Всё из 8-9, плюс:
- ✅ 6 витрин
- ✅ `dbt_project_evaluator`
- ✅ CI в GitHub Actions
- ✅ Инкрементальная загрузка (incremental-модель) **или** история изменений SCD2 (snapshot)
- ✅ Проект работает на двух таргетах из: DuckDB / Postgres / ClickHouse — с макросами портабельности для различий в SQL-диалектах

---

## Что сдать

1. PR с каталогом `dbt/` и всеми файлами
2. В описании PR:
   - Версии `dbt-core` и адаптера (адаптеров)
   - Откуда взяты исходные данные: `dbt seed` из kagglehub или таблицы из предыдущих ДЗ
   - Скриншот/лог успешного `dbt build` или `dbt test`
   - Скриншот DAG из dbt Docs
   - Список реализованных витрин, тестов и пакетов
   - Для 10 баллов: ссылка на успешный прогон GitHub Actions, логи сборки на обоих таргетах

---

## Критерии оценки

| Баллы | Кол-во витрин для реализации | Требования |
|-------|------------------------------|------------|
| 6-7   | 2 | Исходные данные загружены полностью + макрос + пакеты (dbt_utils, dbt_date) + schema.yml с тестами + 1 singular test |
| 8-9   | 4 | + 3–5 singular tests + 1–3 unit tests + 2 пакета для QA (любые из audit_helper / dbt_expectations / elementary / …) + pre-commit (sqlfluff, dbt parse, хук проверки dbt-проекта) + Makefile или justfile |
| 10    | 6 | + dbt_project_evaluator + GitHub Actions + incremental или snapshot (SCD2) + 2 таргета (любые из DuckDB / Postgres / ClickHouse) с макросами портабельности |
