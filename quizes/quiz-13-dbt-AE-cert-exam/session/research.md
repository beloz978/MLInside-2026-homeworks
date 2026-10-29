# Факты об экзамене и источники

Проверено 15.10.2026 по официальным страницам dbt Labs.

## Формат

| Параметр | Значение |
|---|---|
| Экзамен | dbt Analytics Engineering Certification, dbt Core 1.11 |
| Вопросов | 65, каждый за 1 балл, веса одинаковы |
| Время | 2 часа, онлайн-прокторинг (регистрация через Talview) |
| Проходной балл | 65% (≈ 43 правильных ответа из 65), результат показывается сразу |
| Цена | $200; пересдача требует новой оплаты |
| Срок действия сертификата | 2 года |
| Рекомендуемый опыт | SQL и 6+ месяцев работы с dbt или dbt Core |
| Языки | страница экзамена: английский, японский, испанский, французский, португальский; страница study guide: английский и японский (расхождение между страницами) |

Веса доменов dbt Labs не публикует.

## Домены и подтемы (study guide 1.11)

1. Developing and optimizing dbt models: зависимости от сырых объектов; материализации; модульность и DRY; команды `build`, `run`, `test`, `docs`, `show`, `snapshot`, `seed`; логичные DAG; конфиги в `dbt_project.yml`; пакеты; Python-модели; `grants`; снапшоты в YAML; выбор стратегии incremental; `--empty`; `--sample`; microbatch.
2. Managing dbt models governance: contracts, versions и deprecation, constraints.
3. Debugging data modeling errors: сообщения об ошибках, compiled code, ошибки YAML, исправление и проверка до merge, флаги.
4. Troubleshooting and optimizing dbt pipelines: точки отказа в DAG, `dbt clone`.
5. Implementing dbt tests: generic, singular, custom, custom generic, unit tests; проверка допущений для моделей и источников.
6. Implementing and maintaining external dependencies: exposures, source freshness (название домена на странице читается неоднозначно).
7. Leveraging the dbt state: state и выбор по state, `dbt retry`.

## Источники

- [dbt certificate study guide, версия 1.11](https://www.getdbt.com/dbt-assets/certifications/dbt-certificate-study-guide-version-1-11)
- [dbt Analytics Engineering Certification Exam (страница экзамена)](https://www.getdbt.com/certifications/analytics-engineer-certification-exam-version-1-11)

В поиске попались сторонние страницы (study guide на сторонних сайтах, практические тесты на платформах курсов); они не открывались и не использовались. Дампы и «реальные вопросы» не применялись: это нарушает условия экзамена.
