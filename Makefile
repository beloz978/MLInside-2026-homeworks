# Тесты курса в терминале: `make quiz 4` → quizes/test-4-*.yaml (нужен uv).

.DEFAULT_GOAL := help
.PHONY: help quiz

NR := $(word 2,$(MAKECMDGOALS))
QUIZ := $(firstword $(wildcard quizes/test-$(NR)-*.yaml))

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-8s %s\n", $$1, $$2}'

quiz: ## Пройти тест: make quiz <номер>, например make quiz 4
	@test -n "$(NR)" || { echo "Укажите номер: make quiz 4"; exit 1; }
	@test -n "$(QUIZ)" || { echo "Нет quizes/test-$(NR)-*.yaml (сделайте его через quizes/md2yaml.py)"; exit 1; }
	uv run --with questionary --with pyyaml python quizes/quiz.py $(QUIZ)

# the number after `quiz` is an argument, not a target
ifeq (quiz,$(firstword $(MAKECMDGOALS)))
$(NR):
	@:
endif
