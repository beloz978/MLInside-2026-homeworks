# MLInside 2026 — домашние задания (dbt + Dagster, датасет Olist)

Минимальный набор для сдачи и самопроверки двух домашних заданий курса MLInside 2026:

| Каталог | Что там |
|---|---|
| [`dbt/`](dbt/README.md) | ДЗ по **dbt**: [инструкция](dbt/MANUAL.md), [текст задания](dbt/ДЗ/ДЗ_dbt_Olist.md) и **автопроверка** — `make check` ставит оценку «N из 10» |
| [`Dagster/`](Dagster/README.md) | ДЗ по **оркестрации в Dagster**: [текст задания](Dagster/ДЗ/ДЗ_Dagster_Olist.md). Берёт dbt-проект из первого ДЗ и оркестрирует его (на высшую оценку — до обученной модели). Автопроверки для Dagster здесь нет |

## Быстрый старт (dbt)

Нужны: [uv](https://docs.astral.sh/uv/), `make`, `git`, готовый dbt-проект. Команды — из каталога `dbt/`, по одной:

```bash
cd dbt
make setup    # 1. .venv и зависимости
make wizard   # 2. мастер: GitHub, путь к вашему проекту, Postgres/ClickHouse -> .env и .env.local
make seeds    # 3. скачать Olist (kagglehub) в seeds/ вашего проекта; затем в проекте: dbt deps && dbt seed
make ready    # 4. проверка готовности: инструменты, пути, доступность СУБД
make check    # 5. итог: «Проект прошёл на N из 10 баллов» и список недостающего
```

Все пять шагов подряд: `make run`. Список команд: `make help`. Подробности — в [`dbt/MANUAL.md`](dbt/MANUAL.md).

## Что внутри `dbt/`

| Файл | Зачем |
|---|---|
| [`MANUAL.md`](dbt/MANUAL.md), [`Makefile`](dbt/Makefile) | Инструкция для студента и минимум команд |
| [`scripts/check_hw.py`](dbt/scripts/check_hw.py) | Главный проверяющий скрипт: запускает проект, разбирает `manifest.json`/`run_results.json`, проверяет требования уровней 6–7 / 8–9 / 10, сверяет витрины с эталоном, через GitHub API проверяет PR и CI |
| [`scripts/wizard.py`](dbt/scripts/wizard.py) | Интерактивная настройка; секреты уходят только в `.env.local` |
| [`scripts/doctor.py`](dbt/scripts/doctor.py), [`scripts/check_db_from_profile.py`](dbt/scripts/check_db_from_profile.py) | Проверка окружения и доступности СУБД по вашему `profiles.yml` (DuckDB, Postgres, ClickHouse) |
| [`scripts/fetch_olist_seeds.py`](dbt/scripts/fetch_olist_seeds.py) | Скачивает 8 CSV Olist в `seeds/` вашего проекта |
| [`scripts/envload.py`](dbt/scripts/envload.py), [`scripts/gh_api.py`](dbt/scripts/gh_api.py) | Чтение `.env` / `.env.local`; PR и статус GitHub Actions через REST API |
| [`data/`](dbt/data) | Эталон: контрольные цифры витрин, контракт колонок, ожидания по исходным данным |
| [`.env.example`](dbt/.env.example), [`.env.local.example`](dbt/.env.local.example) | Шаблоны настроек. Абсолютных путей в коде нет — всё берётся из `.env` |
| [`requirements.txt`](dbt/requirements.txt) | Зависимости (драйверы Postgres/ClickHouse — закомментированы) |

## Безопасность

- `.env` и `.env.local` **не коммитятся** (см. [`.gitignore`](.gitignore)): пароли БД и токен GitHub хранятся только локально, `.env.local` создаётся с правами 600.
- Токен GitHub нужен только для проверки PR/CI (права на чтение Pull requests и Actions); без него: `python scripts/check_hw.py --no-gh`.
