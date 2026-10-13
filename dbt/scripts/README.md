# Скрипты самопроверки ДЗ по dbt

Запускаются через [`Makefile`](../Makefile) из каталога `dbt/` (`make help` — список команд); напрямую: `.venv/bin/python scripts/<имя>.py`. Личные пути и настройки берутся из `config/.env` / `config/.env.local` ([шаблоны](../config/.env.example)) — абсолютных путей в коде нет; общие константы (пороги, допуски, URL) — в [`settings.yml`](settings.yml).

| Шаг `make` | Скрипт |
|---|---|
| `make wizard` | [`wizard.py`](wizard.py) |
| `make seeds` | [`fetch_olist_seeds.py`](fetch_olist_seeds.py) |
| `make ready` | [`doctor.py`](doctor.py), затем [`check_db_from_profile.py`](check_db_from_profile.py) |
| `make check` | [`check_hw.py`](check_hw.py) |
| — (используют остальные) | [`envload.py`](envload.py), [`settings.py`](settings.py), [`gh_api.py`](gh_api.py) |

## `check_hw.py` — главная проверка

Запускает ваш dbt-проект, разбирает `manifest.json` и `run_results.json` и печатает отчёт с итогом «Проект прошёл на N из 10 баллов». Проверяет:

- требования уровней **6–7 / 8–9 / 10** из задания (по баллу за критерий);
- полноту исходных данных: 8 таблиц, число строк, ключевые колонки, контрольные суммы — по [`data/raw_expectations.json`](../data/raw_expectations.json);
- витрины против эталона [`data/control_figures.json`](../data/control_figures.json) с допуском; обязательные колонки — [`data/marts_contract.json`](../data/marts_contract.json);
- через GitHub API: PR создан и заполнен, CI зелёный.

Флаги: `--no-gh` (не обращаться к GitHub: критерий про PR и CI при этом не засчитывается), `--no-run` (не запускать dbt, взять готовые `target/` и DuckDB), `--json` (отчёт в JSON), `--min N` (минимальный балл для кода возврата 0, по умолчанию 1).

## `wizard.py` — интерактивная настройка

Спрашивает по шагам: вход в GitHub (через браузер `gh auth login` или вставка токена — ввод скрыт; нужны права на чтение Pull requests и Actions), репозиторий и номер PR; путь к dbt-проекту и `profiles.yml`; второй таргет — нет / Postgres / ClickHouse, хост, порт, пользователь, база, пароль. Несекретное пишет в `config/.env`, токен и пароли — в `config/.env.local` (права 600); прежние файлы сохраняются как `*.bak`. Пароли и токен не печатаются.

Без вопросов (CI/тест): `python scripts/wizard.py --non-interactive --project PATH [--db postgres ...]`.

## `fetch_olist_seeds.py`

Скачивает Olist через `kagglehub.dataset_download()` и кладёт 8 CSV в `seeds/` вашего проекта; `--only-missing` пропускает уже скачанные. Дальше в каталоге проекта: `dbt deps && dbt seed`.

## `doctor.py`

Проверка окружения: инструменты, Python-пакеты, переменные из `config/.env`, существование путей и файла с эталонными цифрами.

## `check_db_from_profile.py`

Проверяет доступность СУБД по кредам из вашего `profiles.yml` (DuckDB, Postgres, ClickHouse): TCP-соединение и `SELECT 1`. Пароли в вывод не попадают. Код возврата 0/1, есть `--json`.

## `envload.py`

Мини-загрузчик `config/.env` и `config/.env.local` без внешних зависимостей. Приоритет: переменные окружения > `.env.local` > `.env`.

## `settings.yml` и `settings.py`

Общие несекретные константы скриптов, по секции на скрипт: пороги и названия уровней в `check_hw`, список файлов Olist и id датасета Kaggle в `fetch_olist_seeds`, URL, таймауты и регулярки в `gh_api`, порты по умолчанию в `wizard`, списки инструментов, пакетов и переменных в `doctor`. Читаются строго через `settings.py`: нет секции или ключа — `ValueError` с именем ключа. Разделение: `settings.yml` — общее для всех, `config/.env` — личные пути и таргеты, `config/.env.local` — секреты.

## `gh_api.py`

Вспомогательный модуль: данные Pull request и статус GitHub Actions через REST API. Токен берётся из `GH_TOKEN` / `GITHUB_TOKEN` (в том числе из `.env.local`) или из `gh auth token --user <владелец репозитория>`, затем из активного аккаунта gh. Для репозиториев `dataengy/*` нужен аккаунт `dataengy`: на приватном репозитории чужой аккаунт получает 404 «Not Found», а не 403.
