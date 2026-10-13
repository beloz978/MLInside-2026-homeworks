# ДЗ по dbt (Olist) — самопроверка

Набор скриптов, чтобы убедиться, что окружение и ваш dbt-проект работают, и получить оценку **«N из 10»** по критериям задания. Текст задания: [ДЗ/ДЗ_dbt_Olist.md](ДЗ/ДЗ_dbt_Olist.md). Короткая пошаговая инструкция: [MANUAL.md](MANUAL.md). Описание скриптов: [scripts/README.md](scripts/README.md).

## Быстрый старт

Нужны: [uv](https://docs.astral.sh/uv/), `make`, `git` и ваш dbt-проект. Windows: `make` есть в Git Bash/WSL или `winget install ezwinports.make`. Команды — из этого каталога, по одной:

```bash
make setup    # 1. .venv и зависимости
make wizard   # 2. мастер: GitHub, путь к проекту, Postgres/ClickHouse -> config/.env и config/.env.local
make seeds    # 3. скачать Olist (kagglehub) в seeds/ вашего проекта
              #    затем в каталоге проекта: dbt deps && dbt seed
make ready    # 4. проверка готовности: инструменты, пути, доступность СУБД
make check    # 5. итог: «Проект прошёл на N из 10 баллов» и список недостающего
```

Все шаги подряд: `make run`. Список команд: `make help`. Что делает каждый шаг и какие у него флаги — в [scripts/README.md](scripts/README.md).

## Файлы

| Файл | Зачем |
|---|---|
| [`Makefile`](Makefile) | Минимум команд для студента |
| [`scripts/`](scripts) | Скрипты проверки, см. [scripts/README.md](scripts/README.md) |
| [`data/`](data) | Эталонные цифры, контракт колонок, ожидания по исходным данным |
| [`config/`](config) | Настройки: шаблоны [`.env.example`](config/.env.example) и [`.env.local.example`](config/.env.local.example), [`requirements.txt`](config/requirements.txt) (драйверы Postgres/ClickHouse — закомментированы) |
| [`scripts/settings.yml`](scripts/settings.yml) | Общие константы скриптов (пороги баллов, допуски, список витрин, URL GitHub API, таймауты) |

## Секреты

`config/.env` и `config/.env.local` не коммитятся (см. `.gitignore` в корне репозитория). Токену GitHub нужны только права на чтение Pull requests и Actions.

Следующее ДЗ строится на этом проекте: [оркестрация в Dagster](../Dagster/README.md).
