# Тесты курса в терминале: `make quiz 4` → quizes/test-4-*.yaml (нужен uv).

.DEFAULT_GOAL := help
.PHONY: help quiz quiz-yaml quiz-test

NR := $(word 2,$(MAKECMDGOALS))
QUIZ := $(firstword $(wildcard quizes/test-$(NR)-*.yaml))
QUIZ_MD := $(firstword $(wildcard quizes/test-$(NR)-*.md))

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-10s %s\n", $$1, $$2}'

quiz: ## Пройти тест: make quiz <номер>, например make quiz 4
	@test -n "$(NR)" || { echo "Укажите номер: make quiz 4"; exit 1; }
	@test -n "$(QUIZ)" || { echo "Нет quizes/test-$(NR)-*.yaml (сделайте его: make quiz-yaml $(NR))"; exit 1; }
	uv run --with questionary --with pyyaml python quizes/quiz.py $(QUIZ)

quiz-yaml: ## md → yaml с самопроверкой: make quiz-yaml <номер> [SECTION="<заголовок раздела>"]
	@test -n "$(NR)" || { echo "Укажите номер: make quiz-yaml 4"; exit 1; }
	@test -n "$(QUIZ_MD)" || { echo "Нет quizes/test-$(NR)-*.md"; exit 1; }
	uv run --with pyyaml python quizes/md2yaml.py $(QUIZ_MD) $(if $(SECTION),"$(SECTION)")

quiz-test: ## Тесты клавиш quiz.py (pytest)
	uv run --with questionary --with pyyaml --with pytest pytest quizes/test_quiz.py

# the number after `quiz`/`quiz-yaml` is an argument, not a target
ifneq (,$(filter quiz quiz-yaml,$(firstword $(MAKECMDGOALS))))
$(NR):
	@:
endif
