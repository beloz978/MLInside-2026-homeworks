# ДЗ по dbt (Olist) — самопроверка

Набор скриптов, чтобы убедиться, что окружение и ваш dbt-проект работают, и получить оценку **«N из 10»** по критериям задания. Текст задания: [ДЗ/ДЗ_dbt_Olist.md](ДЗ/ДЗ_dbt_Olist.md). Короткая пошаговая инструкция: [MANUAL.md](MANUAL.md).

## Быстрый старт

Нужны: [uv](https://docs.astral.sh/uv/), `make`, `git` и ваш dbt-проект. Windows: `make` есть в Git Bash/WSL или `winget install ezwinports.make`. Команды — из этого каталога, по одной:

```bash
make setup    # 1. .venv и зависимости
make wizard   # 2. мастер: GitHub, путь к проекту, Postgres/ClickHouse -> .env и .env.local
make seeds    # 3. скачать Olist (kagglehub) в seeds/ вашего проекта
              #    затем в каталоге проекта: dbt deps && dbt seed
make ready    # 4. проверка готовности: инструменты, пути, доступность СУБД
make check    # 5. итог: «Проект прошёл на N из 10 баллов» и список недостающего
```

Все шаги подряд: `make run`. Список команд: `make help`.

## Что проверяет `make check`

`scripts/check_hw.py` запускает ваш проект, разбирает `manifest.json` и `run_results.json` и проверяет:

- требования уровней **6–7 / 8–9 / 10** из задания (по баллу за критерий);
- полноту исходных данных: 8 таблиц, число строк, ключевые колонки, контрольные суммы (`data/raw_expectations.json`);
- витрины против эталона `data/control_figures.json` с допуском; обязательные колонки — `data/marts_contract.json`;
- через GitHub API: PR создан и заполнен, CI зелёный.

Полезные флаги: `--no-gh` (без GitHub), `--no-run` (по уже собранным артефактам `target/`), `--json` (отчёт в JSON). Код возврата 0, если набрано не меньше `--min` баллов.

## Файлы

| Файл | Зачем |
|---|---|
| [`Makefile`](Makefile) | Минимум команд для студента |
| [`scripts/wizard.py`](scripts/wizard.py) | Интерактивная настройка; несекретное — в `.env`, токен и пароли — в `.env.local` (права 600), прежние файлы сохраняются как `*.bak`. Без вопросов: `python scripts/wizard.py --non-interactive --project PATH` |
| [`scripts/fetch_olist_seeds.py`](scripts/fetch_olist_seeds.py) | Скачивает 8 CSV Olist в `seeds/` вашего проекта |
| [`scripts/doctor.py`](scripts/doctor.py) | Проверка окружения: инструменты, пакеты, переменные, пути |
| [`scripts/check_db_from_profile.py`](scripts/check_db_from_profile.py) | Доступность СУБД по `profiles.yml` (DuckDB, Postgres, ClickHouse): TCP + `SELECT 1`; пароли в вывод не попадают |
| [`scripts/check_hw.py`](scripts/check_hw.py) | Главная проверка, см. выше |
| [`scripts/envload.py`](scripts/envload.py), [`scripts/gh_api.py`](scripts/gh_api.py) | Чтение `.env` / `.env.local`; PR и статус GitHub Actions через REST API |
| [`data/`](data) | Эталонные цифры, контракт колонок, ожидания по исходным данным |
| [`.env.example`](.env.example), [`.env.local.example`](.env.local.example) | Шаблоны настроек. Абсолютных путей в коде нет — всё берётся из `.env` |
| [`requirements.txt`](requirements.txt) | Зависимости (драйверы Postgres/ClickHouse — закомментированы) |

## Секреты

`.env` и `.env.local` не коммитятся (см. `.gitignore` в корне репозитория). Токену GitHub нужны только права на чтение Pull requests и Actions; без токена запускайте проверку без GitHub: `.venv/bin/python scripts/check_hw.py --no-gh`.

Следующее ДЗ строится на этом проекте: [оркестрация в Dagster](../Dagster/README.md).
