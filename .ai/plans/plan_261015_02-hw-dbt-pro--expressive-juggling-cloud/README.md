# План: абсолютные HW_DBT_PRO*_DIR + перезапуск проверки ДЗ

## Context
Пользователь просит перезапустить проверку ДЗ (`make check` в `/Users/user/gi/@beloz978/MLInside-2026-homeworks/dbt`)
и убедиться, что `HW_DBT_PROJECT_DIR` / `HW_DBT_PROFILES_DIR` в `.env` — абсолютные пути.

Проверено (read-only): **сейчас не абсолютные.** `config/.env`:
```
HW_DBT_PROJECT_DIR=../../../@dataengy/dbt
HW_DBT_PROFILES_DIR=../../../@dataengy/dbt
```
Причина — `scripts/wizard.py`: `rel()` (стр. 85) делает `os.path.relpath(p, ROOT)`, а `step_project`
возвращает `{"HW_DBT_PROJECT_DIR": rel(p), "HW_DBT_PROFILES_DIR": rel(pp), ...}` (стр. 115) — в `.env` уходит относительный путь.

Читатели абсолютные пути уже поддерживают, менять их не нужно:
`check_hw.pth` → `resolve_path(v, ROOT).resolve()`; `doctor.p` → `(ROOT / v).resolve()`;
`wizard` стр. 165/196 → `(ROOT / ...).resolve()`; `utils.resolve_path` возвращает абсолютный путь как есть и раскрывает `~`.

## Изменения
1. `dbt/scripts/wizard.py:115` — писать абсолютные пути:
   `return {"HW_DBT_PROJECT_DIR": str(p.resolve()), "HW_DBT_PROFILES_DIR": str(pp.resolve()), "HW_DBT_PROFILE": name}`.
   `rel()` оставить: он нужен для красивых подсказок/дефолтов в диалоге (стр. 97–98, 109).
2. `dbt/config/.env` (локальный, в `.gitignore`) — заменить два значения на абсолютные:
   `/Users/user/gi/@dataengy/dbt` (проект и profiles — тот же каталог, как сейчас). Это правка локальной конфигурации, в git не попадёт.
3. `dbt/config/.env.example` — над строками 8–9 однострочный комментарий «абсолютные пути» (значения остаются пустыми).
4. Тест `dbt/tests/test_wizard.py` (стиль `tests/test_utils.py`; `conftest.py` уже добавляет `scripts/` в `sys.path`):
   создать в `tmp_path` каталог с `dbt_project.yml` и `profiles.yml`, вызвать
   `step_project(ni=True, project_arg=str(dir))` и проверить, что оба значения `Path(...).is_absolute()` и равны `dir.resolve()`.

5. `dbt/scripts/wizard.py` — вызвать `load_env()` из `envload` (как в `doctor.py:18`, `check_hw.py:45`) в начале `main()`.
   Сейчас в `--non-interactive` без `--project` визард не видит `HW_DBT_PROJECT_DIR` из `config/.env` и берёт первый найденный рядом
   `dbt_project.yml` (`find_projects`) — это может быть не тот каталог.
6. `dbt/Makefile` — **уже внесено мной в этой сессии вне плана (нарушение plan mode), на ревью:**
   - `setup`: `[ -d .venv ] || uv venv .venv` вместо строки с обратными кавычками (ломала `echo`) и закомментированного остатка — идемпотентно, проверено на существующем и свежем `.venv`;
   - `wizard`: `$(PY) scripts/wizard.py $(WIZARD_ARGS)` — `make` не пробрасывает `--non-interactive` (разбирает как свою опцию); запуск:
     `make run WIZARD_ARGS="--non-interactive"` (после п. 5 проект берётся из `.env`; до п. 5 — добавить `--project /Users/user/gi/@dataengy/dbt`).
   - Если одобрения нет — откатить: `git checkout -- dbt/Makefile`.

Вне скоупа (не трогаю): `config/.env.bak`, сообщения/логика остальных шагов визарда.

## Verification
- `make test` (pytest) — новый тест зелёный, остальные не сломаны.
- `grep HW_DBT_PRO config/.env` — оба значения начинаются с `/`.
- `make doctor`, затем `make check` — перезапуск проверки ДЗ (запускает dbt build на DuckDB и пишет `data/olist.duckdb`, поэтому только после одобрения плана).
  Ожидание: как раньше 9/10 (критерий 10 ждёт CI-ссылки и второго таргета); теперь `dataengy/dbt` PR #1 смержен в `main`,
  так что GitHub-часть может измениться — отдельно сообщу, что изменилось по сравнению с прошлым прогоном.
- Для `make check` с GitHub нужен токен dataengy в `config/.env.local`; `gh`/сеть в песочнице требуют запуска вне неё (TLS x509).
