# Студенческий минимум: подготовить -> проверить готовность -> получить оценку.
# Всё остальное (детальные проверки, отладка, GitHub, СУБД) — в Justfile (`just`).
# Windows: make есть в Git Bash/WSL или `winget install ezwinports.make`.

PY := $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,.venv/bin/python)

.DEFAULT_GOAL := help
.PHONY: help setup wizard seeds ready check test

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-8s %s\n", $$1, $$2}'

setup: ## 1. Создать .venv и поставить зависимости (нужен uv)
	[ -d .venv ] || uv venv .venv
	uv pip install --python $(PY) -r config/requirements.txt

wizard: ## 2. Мастер настройки: GitHub, путь к проекту, Postgres/ClickHouse -> .env
	$(PY) scripts/wizard.py $(WIZARD_ARGS)

seeds: ## 3. Скачать Olist через kagglehub в seeds/ вашего проекта (затем dbt seed)
	$(PY) scripts/fetch_olist_seeds.py --only-missing

ready: ## 4. Проверка готовности: инструменты, пути, доступность СУБД
	$(PY) scripts/doctor.py
	$(PY) scripts/check_db_from_profile.py

check: ## 5. Финальная проверка: баллы за ДЗ (N из 10)
	$(PY) scripts/check_hw.py

test: ## Тесты скриптов (pytest)
	$(PY) -m pytest tests -q

run: setup wizard seeds ready check
