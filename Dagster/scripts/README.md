# Скрипты автопроверки ДЗ по Dagster

[Задание](../ДЗ/ДЗ_Dagster_Olist.md) выполняется в вашем собственном проекте Dagster (вместе с dbt-проектом из [ДЗ по dbt](../../dbt/README.md)). Здесь — скрипты, которые ставят оценку «N из 10». План и состояние: [`../PLAN.md`](../PLAN.md).

| Файл | Что делает |
|---|---|
| `check_hw.py` | Автопроверка: 10 критериев по 1 баллу. **Сейчас проверяются критерии 1–6** (граф, raw-слой, dbt в графе, checks, расписание, README и PR), максимум — 6 баллов, то есть уровень «6–7». Критерии 7–10 появятся позже |
| `inspect_defs.py` | Описывает проект студента в JSON: ассеты, checks, расписания, сенсоры; итоги запусков из `DAGSTER_HOME`. Запускается интерпретатором **вашего** проекта (там стоит dagster) |
| `settings.yml` | Пороги, регулярки, таймауты, названия критериев, команды |
| `../../dbt/scripts/*` | Общие скрипты: `doctor.py` (`--settings`), `criteria.py` (модель критериев и отчёт), `olist_data.py` (сверка данных Olist), `gh_api.py` (PR и CI), `envload.py`, `settings.py` |

Эталонные цифры (`raw_expectations.json`, `control_figures.json`, `marts_contract.json`) общие с ДЗ по dbt: [`../../dbt/data`](../../dbt/data).

## Как запускать

```bash
cd Dagster
make setup      # .venv и config/.env из шаблона
# заполните config/.env: HW_DAGSTER_PROJECT_DIR, HW_DAGSTER_MODULE, OLIST_DUCKDB_PATH
make ready      # проверка окружения и путей
make check      # полный прогон: материализация графа + сверка с эталоном + GitHub
```

Флаги `check_hw.py`: `--no-run` (без материализации: граф и уже загруженные данные), `--no-gh` (без GitHub; критерий 6 не будет пройден, максимум 5), `--json`, `--min N`, `--settings файл`.

Что должно быть готово в вашем проекте до `make check`: собранный `manifest.json` dbt и CSV Olist в `seeds/` (если грузите через `dbt seed`). Интерпретатор проекта: `HW_DAGSTER_PYTHON` или `.venv` в каталоге проекта.

## Тесты

`make test` (из `Dagster/`): фикстуры-проекты `tests/fixtures/{empty,tier7}`, оценка на синтетических данных, сквозной запуск на `empty`. Тесты `dbt/` и `Dagster/` запускайте отдельно: у них одноимённые `check_hw.py` и `conftest.py`.
