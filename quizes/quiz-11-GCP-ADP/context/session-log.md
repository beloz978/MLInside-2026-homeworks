# Ход сессии и решения

## 2026-10-06 · Оценка исходного квиза
- Вывод: темы верные (S1/S2 гайда), но вопросы проще экзамена: абсурдные дистракторы (JPEG, PNG, SUM(user_id)), подсказки в условии, короткие условия, нет «Choose two», уклон в синтаксис SQL, governance и оркестрация пока не покрыты.
- Предложено: сценарий 3–5 предложений + бизнес-ограничение, 4 правдоподобных GCP-варианта, ~15% multiple select, теги доменов.

## 2026-10-06 · Углубление
- Дампы: разобраны Exam Terms §3, §5.a.vi–vii, §5.a.xi, §8 (см. exam-facts.md). Решение: вопросы пишем сами по гайду и документации.
- Разобраны external / BigLake / native таблицы, column-level security (policy tags, Fine-Grained Reader, dynamic masking, row access policies), оценки стоимости и задержек для 100M × 50 колонок и 7 вариантов архитектуры с ClickHouse (см. analysis-bq-tables-clickhouse.md).
- Написан промпт v2 (quiz-prompt-v2.md) и пробный экзамен #1: вопросы 1–19 переписаны в экзаменационном стиле на английском; план 60 вопросов 18/16/11/15. Сохранено в проект MyCerts: `claude/adp-quiz-prompt.md`, `claude/adp-mock-bank.md`, `claude/adp-mock-key.md`.

## 2026-10-16 · Тест 5 по образцу quiz-4-dagster
- Создан `quiz-5-gcp-adp` той же структуры (quiz.ru.md → quiz.yaml через md2yaml.py, settings.yml, Justfile, README, logs/): 10 основных + 9 резервных вопросов (вопросы 1–19 пробного экзамена). Разбор на русском с тегом домена.
- Формат файла md: вопросы на английском (как на экзамене), служебные слова — русские, потому что парсер и интерфейс используют lang.ru.

## 2026-10-16 · Экзаменационные условия
- Тест расширен до 60 вопросов (как максимум на экзамене) с пропорциями доменов гайда: S1 18, S2 16, S3 11, S4 15. 19 прежних + 41 новый по всем пунктам 1.1–4.4 (Transfer Appliance, dual-region + turbo replication, object tables, Bigtable, Data Fusion, Dataplex DQ, bq load, Spanner, Looker/LookML, Looker Studio credentials, Colab Enterprise, BQML классификация/ARIMA_PLUS/ML.PREDICT, remote models Gemini, Model Registry, Dataform, scheduled queries, Composer, Workflows, Eventarc, Dataflow job UI, Logging, Monitoring alerts, Dataproc Workflow Templates, IAM least privilege, uniform bucket-level access, public access prevention, signed URLs, Analytics Hub, storage classes, lifecycle, dataset expiration, Bucket Lock, table snapshots, Cloud SQL HA и cross-region replica, CMEK, CSEK, encryption at rest/in transit).
- В файле домены перемешаны пропорционально; каждый вопрос получил строку «Тема:» с доменом — по ней работают пресеты (`topics`) и видна разбивка.
- Сложность: простой 20, средний 31, сложный 9; уровни 🟩 17, 🟨 34, 🟥 9; «Choose two» — 7 вопросов (~12%).
- Пресеты теста (`presets.yaml`): `exam` — по умолчанию в Justfile (`just` = экзамен): 60 вопросов, mode exam (разбор в конце), random order, mixed topics, shuffle_options, без подсказок, ru. Также `practice`, `drill`, `domain-s4` (тренировка домена), `mini-exam` (20 случайных).
- `hint_difficulties: []` в settings.yml теста: на экзамене подсказок нет, и не у всех новых вопросов они есть.
- Общий код в `quizes/src` параллельно развивался в другой сессии (presets, exam mode), поэтому в нём ничего не менялось. Пробелы до полного соответствия экзамену перечислены в README.md этой папки.

## 2026-10-16 · Переименование
- Папка `quiz-5-gcp-adp` переименована в `quiz-11-GCP-ADP` (тест 11); ссылки в README и settings.yml обновлены. Упоминания старого имени в истории сессии выше оставлены как есть.
