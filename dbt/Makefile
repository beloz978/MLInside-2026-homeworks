# Студенческий минимум: подготовить -> проверить готовность -> получить оценку.
# Детали каждого шага и флаги скриптов — в scripts/README.md.
# Windows: make есть в Git Bash/WSL или `winget install ezwinports.make`.

VENV := .venv
PY := $(if $(wildcard $(VENV)/Scripts/python.exe),$(VENV)/Scripts/python.exe,$(VENV)/bin/python)
STEPS := setup wizard seeds ready check

.DEFAULT_GOAL := help
.PHONY: help setup wizard seeds ready check test run

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-8s %s\n", $$1, $$2}'

setup: ## 1. Создать .venv и поставить зависимости (нужен uv)
	@if [ -d $(VENV) ]; then echo "🆗 $(VENV) уже есть"; else uv venv $(VENV); fi
	uv pip install --python $(PY) -r config/requirements.txt

wizard: ## 2. Мастер настройки: GitHub, путь к проекту, Postgres/ClickHouse -> .env
	$(PY) scripts/wizard.py

seeds: ## 3. Скачать Olist через kagglehub в seeds/ вашего проекта (затем dbt seed)
	$(PY) scripts/fetch_olist_seeds.py --only-missing

ready: ## 4. Проверка готовности: инструменты, пути, доступность СУБД
	$(PY) scripts/doctor.py
	$(PY) scripts/check_db_from_profile.py

check: ## 5. Финальная проверка: баллы за ДЗ (N из 10)
	$(PY) scripts/check_hw.py

test: ## Тесты скриптов (pytest)
	$(PY) -m pytest tests -q

# Шаги по очереди, а не prerequisites: PY вычисляется при разборе Makefile, а .venv создаёт первый шаг.
# Между шагами — пустая строка; первый упавший шаг останавливает цепочку.
run: ## 0. Всё сразу: setup, wizard, seeds, ready, check
	@for s in $(STEPS); do echo "▶ make $$s"; $(MAKE) --no-print-directory $$s || exit $$?; echo; done
