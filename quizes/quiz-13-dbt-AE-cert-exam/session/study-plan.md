# План подготовки к dbt Analytics Engineering Certification (4 недели)

Выдан в начале сессии. Исходные допущения: dbt уже используется в проектах (DEJAP и др.), 8–10 часов в неделю, целевая дата экзамена не задана.

## Приоритеты по доменам

| Домен | Что точно проверят | Приоритет |
|---|---|---|
| 1. Models | материализации, стратегии incremental (append, merge, delete+insert, insert_overwrite, microbatch), `dbt_project.yml`, пакеты, Python-модели, `grants`, snapshots в YAML, `--empty`, `--sample` | Высокий, самый объёмный |
| 2. Governance | contracts, model versions и deprecation, constraints | Высокий, часто упускают |
| 3. Debugging | логи, `target/compiled` и `target/run`, ошибки YAML, флаги | Средний |
| 4. Pipelines | сбои в DAG, `dbt clone` | Средний |
| 5. Tests | generic, singular, custom generic, unit tests, severity, `store_failures` | Высокий |
| 6. External deps | sources, source freshness, exposures | Средний |
| 7. State | `state:modified`, `--defer`, `--state`, `dbt retry`, slim CI | Высокий, вопросы каверзные |

## Недели

- Неделя 1. Диагностика (study guide, sample questions) и домен 1: стратегии incremental по адаптерам, microbatch на модели DEJAP, `--empty` и `--sample`, snapshots в YAML, `grants`, Python-модели; заметки на страницу по каждому домену.
- Неделя 2. Домены 2 и 5: contract + constraints (что реально enforced на платформе), версия модели с `deprecation_date`, все виды тестов (в т.ч. unit с мок-входами), severity, `warn_if` / `error_if`, `store_failures`.
- Неделя 3. Домены 3, 4, 6, 7: намеренно ломать проект и читать ошибки, сравнивать `compiled/` и `run/`; `dbt retry`, `dbt clone`, `state:modified+`, `--defer` и slim CI на двух `target`; source freshness и exposures.
- Неделя 4. Два пробных экзамена по 65 вопросов за 120 минут (цель — не меньше 80% на втором), разбор ошибок и «угаданных» ответов, за 2 дня до экзамена только свои заметки; техническая проверка прокторинга.

## Источники подготовки

Официальный study guide и sample questions; документация dbt по темам (incremental, contracts, versions, unit tests, state, retry); практика на своих проектах; курсы dbt Learn как дополнение. Тренировка — на собственных вопросах по официальному гайду (тест 13).
