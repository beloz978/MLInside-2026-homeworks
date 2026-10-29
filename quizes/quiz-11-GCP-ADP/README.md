# Тест 11. Google Cloud Associate Data Practitioner (ADP)

Пробный экзамен ADP (exam guide v1.0) в условиях, близких к реальным: 60 сценарных вопросов на английском, ~120 минут, домены 18/16/11/15, разбор на русском в конце. Контекст создания и решения — в [`context/`](context/).

| Файл | Что там |
|---|---|
| [`quiz.ru.md`](quiz.ru.md) | Текст теста (источник правды) |
| `quiz.yaml` | Сгенерированный из md файл для `quiz.py` |
| [`settings.yml`](settings.yml) | Настройки этого теста поверх [базовых](../src/settings.yml) |
| [`logs/`](logs/) | Логи прохождений (JSONL, в git) |
| [`Justfile`](Justfile) | Команды запуска из этого каталога |
| [`presets.yaml`](presets.yaml) | Пресеты теста: `exam` (по умолчанию), `practice`, `drill`, `domain-s4`, `mini-exam` |
| [`context/`](context/) | Контекст сессии: решения, факты об экзамене, источники |

## Запуск

```bash
just            # экзамен (пресет exam по умолчанию)
just run practice   # тренировка с разбором после каждого ответа
just presets    # все пресеты: exam, practice, drill, domain-s4, mini-exam
just yaml       # quiz.ru.md → quiz.yaml
just logs       # последние логи
```

Домены экзамена: S1 Data preparation and ingestion (~30%), S2 Data analysis and presentation (~27%), S3 Data pipeline orchestration (~18%), S4 Data management (~25%). Домен указан в строке «Тема:» каждого вопроса и в начале «Разбора».

Формат теста и правила правки — в [`../README.md`](../README.md#формат-теста-и-правила-правки).
