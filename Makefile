# Тесты курса в терминале: `make quiz 4` → quizes/quiz-4-*/ (нужен uv).

.DEFAULT_GOAL := help
.PHONY: help quiz quiz-yaml quiz-test

NR := $(word 2,$(MAKECMDGOALS))
QUIZ_DIR := $(firstword $(wildcard quizes/quiz-$(NR)-*/))

help: ## Список команд
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | awk -F'\t' '{printf "  make %-10s %s\n", $$1, $$2}'

quiz: ## Пройти тест: make quiz <номер> [QUIZ_LANG=ru|en], например make quiz 4
	@test -n "$(NR)" || { echo "Укажите номер: make quiz 4"; exit 1; }
	@test -n "$(QUIZ_DIR)" || { echo "Нет каталога quizes/quiz-$(NR)-*/"; exit 1; }
	@test -f $(QUIZ_DIR)quiz.yaml || { echo "Нет $(QUIZ_DIR)quiz.yaml (сделайте его: make quiz-yaml $(NR))"; exit 1; }
	uv run --with questionary --with pyyaml python quizes/src/quiz.py $(QUIZ_DIR) $(if $(QUIZ_LANG),--lang $(QUIZ_LANG))

quiz-yaml: ## md → yaml с самопроверкой: make quiz-yaml <номер> [SECTION="<заголовок раздела>"]
	@test -n "$(NR)" || { echo "Укажите номер: make quiz-yaml 4"; exit 1; }
	@test -n "$(QUIZ_DIR)" || { echo "Нет каталога quizes/quiz-$(NR)-*/"; exit 1; }
	uv run --with pyyaml python quizes/src/md2yaml.py $(QUIZ_DIR) $(if $(SECTION),"$(SECTION)")

quiz-test: ## Тесты клавиш quiz.py (pytest)
	uv run --with questionary --with pyyaml --with pytest pytest quizes/src/test_quiz.py

# the number after `quiz`/`quiz-yaml` is an argument, not a target
ifneq (,$(filter quiz quiz-yaml,$(firstword $(MAKECMDGOALS))))
$(NR):
	@:
endif
