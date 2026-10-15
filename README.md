# MLInside 2026 — домашние задания (dbt + Dagster, датасет Olist)

Минимальный набор для сдачи и самопроверки двух домашних заданий курса MLInside 2026.

| Каталог | Что там |
|---|---|
| [`dbt/`](dbt/README.md) | ДЗ по **dbt**:<ul><li>сначала — [тест 3 «dbt»](quizes/quiz-3-dbt-review/quiz.ru.md): `make quiz 3`</li><li>[текст задания](dbt/ДЗ/ДЗ_dbt_Olist.md)</li><li>[инструкция по самопроверке](dbt/MANUAL.md)</li><li>[**автопроверка**](dbt/Makefile#L28) — `make check` ставит оценку «N из 10»</li></ul> |
| [`Dagster/`](Dagster/README.md) | ДЗ по **оркестрации в Dagster**:<ul><li>сначала — [тест 4 «Dagster»](quizes/quiz-4-dagster/quiz.ru.md): `make quiz 4`</li><li>[текст задания](Dagster/ДЗ/ДЗ_Dagster_Olist.md) — берёт dbt-проект из первого ДЗ и оркестрирует его (на высшую оценку — до обученной модели)</li><li>[план автопроверки и эталона](Dagster/PLAN.md) — пока не реализованы</li></ul> |
| [`quizes/`](quizes/README.md) | **Тесты** по модулям курса:<ul><li>[тест 4 «Dagster»](quizes/quiz-4-dagster/quiz.ru.md) — 10 вопросов с разбором + 5 резервных</li><li>[ревью теста 3 «dbt»](quizes/quiz-3-dbt-review/quiz.ru.md) — замечания и переписанные варианты</li><li>[формат теста и правила правки](quizes/README.md#формат-теста-и-правила-правки)</li></ul> |

Начните с [`dbt/README.md`](dbt/README.md): там быстрый старт, список файлов и заметки о секретах.
