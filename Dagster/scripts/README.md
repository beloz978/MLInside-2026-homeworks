# Скрипты автопроверки ДЗ по Dagster

[Задание](../ДЗ/ДЗ_Dagster_Olist.md) выполняется в вашем собственном проекте Dagster (вместе с dbt-проектом из [ДЗ по dbt](../../dbt/README.md)). Здесь — скрипты, которые ставят оценку «N из 10». План и состояние: [`../PLAN.md`](../PLAN.md).

| Файл | Что делает |
|---|---|
| `check_hw.py` | Автопроверка: 10 критериев по 1 баллу. **Сейчас проверяются критерии 1–9**: граф, raw-слой, dbt в графе, checks, расписание, README и PR; automation, freshness и секреты; алерт и «Как устроен Dagster»; pre-commit и CI. Максимум — 9 баллов, то есть уровень «8–9». Критерий 10 (dlt и модель) появится позже |
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

Флаги `check_hw.py`: `--no-run` (без материализации: граф и уже загруженные данные), `--no-gh` (без GitHub; критерии 6 и 9 не будут пройдены, максимум 7), `--json`, `--min N`, `--settings файл`.

Что должно быть готово в вашем проекте до `make check`: собранный `manifest.json` dbt и CSV Olist в `seeds/` (если грузите через `dbt seed`). Интерпретатор проекта: `HW_DAGSTER_PYTHON` или `.venv` в каталоге проекта.

## Тесты

Для критериев 7–9 чекер читает файлы вашего проекта: то, что попадёт в репозиторий (`git ls-files`, включая новые неигнорируемые), а также `.pre-commit-config.yaml` и `.github/workflows/` в каталоге проекта или выше. В отчёт выводится только файл, строка и вид найденного секрета, само значение — никогда.

`make test` (из `Dagster/`): фикстуры-проекты `tests/fixtures/{empty,tier7,tier9}`, оценка на синтетических данных, сквозной запуск на `empty`. Тесты `dbt/` и `Dagster/` запускайте отдельно: у них одноимённые `check_hw.py` и `conftest.py`.
