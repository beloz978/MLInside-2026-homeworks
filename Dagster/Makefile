# Студенческий минимум: подготовить -> проверить готовность -> получить оценку.
# Скрипты doctor.py, envload.py, gh_api.py и др. общие с dbt/ (../dbt/scripts), настройки — scripts/settings.yml.

PY := $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,.venv/bin/python)

.DEFAULT_GOAL := help
.PHONY: help setup ready check test

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-8s %s\n", $$1, $$2}'

setup: ## 1. Создать .venv и поставить зависимости (нужен uv); config/.env из шаблона
	uv venv .venv || echo ".venv already exists."
	uv pip install --python $(PY) -r config/requirements.txt
	@test -f config/.env || cp config/.env.example config/.env

ready: ## 2. Проверка готовности: инструменты, пакеты, переменные .env, пути
	$(PY) ../dbt/scripts/doctor.py --settings scripts/settings.yml

check: ## 3. Финальная проверка: баллы за ДЗ (N из 10)
	$(PY) scripts/check_hw.py

test: ## Тесты скриптов (pytest)
	$(PY) -m pytest tests -q
