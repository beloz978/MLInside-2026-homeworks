# Plan: move env/requirements to dbt/config/, slim root README, backlog the MANUAL.md question

## Context
The root `README.md` repeats `dbt/README.md` (quick start, "Что внутри dbt/" table, security). The env templates and
`requirements.txt` sit loose in `dbt/`. Goal: settings files grouped in `dbt/config/`, root README reduced to an index.
`dbt/MANUAL.md` is a near-subset of the `dbt/README.md` quick start, but per the user it is **left as is for now**;
whether to merge it is only recorded as a backlog item.

Decisions (from user): `dbt/MANUAL.md` untouched (backlog: analyze whether it should be merged); Dagster left as is
(it has no MANUAL.md); `config/` lives at **`dbt/config/`**; `.env.local` (written by `make wizard`, gitignored) also goes
to `dbt/config/` so the pair stays together.

## 1. Move files (all under `dbt/`)
- `git mv requirements.txt .env.example .env.local.example config/`
- `mv .env config/.env` (untracked/ignored, holds the user's real settings; plain `mv`, content untouched)
- No `.env.local` exists today. `.gitignore` patterns `.env` / `.env.local` / `.env.*.bak` are unanchored, so they already cover `dbt/config/` — no `.gitignore` change.
- Relative paths *inside* `.env` (e.g. `HW_DBT_PROJECT_DIR`) keep resolving from `dbt/` (`ROOT` unchanged), so the user's `.env` stays valid.

## 2. Code changes (env location only; `ROOT` stays `dbt/` for data/ and relative paths)
- `dbt/scripts/envload.py`: add `ENV_DIR = ROOT / "config"`; `load_env(root: Path = ENV_DIR)`; update docstring. Callers `doctor.py`, `check_hw.py`, `check_db_from_profile.py`, `fetch_olist_seeds.py` call `load_env()` with no args → no edit needed.
- `dbt/scripts/wizard.py`: import `ENV_DIR`; write `ENV_DIR / ".env"` and `ENV_DIR / ".env.local"` (lines ~243, 245); update user-facing strings (~196 `requirements.txt` → `config/requirements.txt`, ~215, ~246).
- `dbt/Makefile` line 16: `-r requirements.txt` → `-r config/requirements.txt`.

## 2b. `dbt/scripts/settings.yml` — non-secret script settings out of the code
Per the global rule (no hardcoded scalars/ids/urls/timeouts/regexes; strict read, no defaults): one tracked YAML, a section per
script. Per-user paths/targets stay in `config/.env`; secrets stay in `config/.env.local`. `settings.yml` holds only shared constants.

New helper `dbt/scripts/settings.py` (~15 lines, pyyaml already a requirement): `section(name) -> dict` reads
`settings.yml` next to the scripts; a missing section/key raises `ValueError` naming the key and the file (no `.get(k, default)`).

Sections and what moves in (current literal → key):
- `check_hw`: `MARTS`, `QA_PACKAGES`, `ORDER_HOOKS` (lines 43–46); `REL_TOL`/`ABS_TOL` (47) → `tolerance.rel/abs`;
  criterion thresholds → `thresholds.*` (marts 2/4/6 at 392/422/445, singular tests ≥3 at 423, unit tests ≥1 at 425, QA pkgs ≥2 at 430,
  PR title ≥5 / body ≥30 at 413–414); `--min` default 1 (482); level cut-offs 6/8/10 + names (473); `segment_values` HIGH/MEDIUM/LOW (220);
  `search_depth` of repo-level files = 2 parents (`search_dirs`); data file names `raw_expectations.json`, `marts_contract.json` (287, 501).
- `fetch_olist_seeds`: `FILES` list, geolocation file name, kaggle dataset id `olistbr/brazilian-ecommerce`.
- `gh_api`: `API` url, `User-Agent`, timeouts 20 / 15 (57, 27, 37), `per_page` values (67–90), the 4 regexes (47, 129–131; single-quoted YAML scalars).
- `check_db_from_profile`: `--timeout` default 5.0 (159).
- `wizard`: `DEFAULTS` per DB (host/port/user/db for postgres, clickhouse), pip-driver hint strings (196).

Deliberately **not** moved: per-mart assertion logic in `check_hw.py` (~194–230, already driven by `data/*.json`), Russian UI strings, argparse flags, algorithm code.
Code reads values via `S = settings.section("check_hw")` → `S["tolerance"]["rel"]`.

**`doctor.py` is skipped in this pass**: it has the user's uncommitted edits (see caveats) and I can't commit my hunks separately
(`git add -p` is interactive). Its tool/package/env-name lists are a ready follow-up once that WIP is committed — say the word.

Order of work: (1) record a baseline (`check_hw.py --no-run --no-gh --json`, `check_db_from_profile.py --json`) **before** touching anything;
(2) create `settings.yml` + `settings.py`; (3) switch each script one at a time; (4) diff outputs against the baseline.

## 3. Docs
- **`dbt/README.md`**: keep structure and the MANUAL link in the intro; only point the "Файлы" table at `config/`
  (`config/.env.example`, `config/.env.local.example`, `config/requirements.txt`) and say in "Секреты" that `config/.env*` is not committed.
- **`dbt/MANUAL.md`: not touched.** Its commands (`make setup/wizard/...`) don't reference moved files, so it stays valid.
- `dbt/scripts/README.md`: `[шаблоны](../.env.example)` → `../config/.env.example`; mention files live in `config/` (lines 3, 26, 36, 44);
  add a short "`settings.yml` / `settings.py`" entry (what goes where: settings.yml = shared constants, `config/.env` = per-user, `.env.local` = secrets).
- `dbt/README.md` "Файлы" table: one row for `scripts/settings.yml`.
- **Root `README.md`** → index only, no repeats of `dbt/README.md`: title + 1–2 line intro; the directory table
  (`dbt/` → README + [инструкция](dbt/MANUAL.md) + task text + «make check → N из 10»; `Dagster/` → README + task text, no autocheck);
  one line "Начать с [`dbt/README.md`](dbt/README.md)". Remove: quick start, "Что внутри `dbt/`" table, "Безопасность"
  (all already in `dbt/README.md`). The `MANUAL.md` link in the table stays.
- **Backlog item** (after approval, via the `add-to-ai-backlog-and-skip-for-now` skill): "MLInside-2026-homeworks: analyze whether
  `dbt/MANUAL.md` should be merged into `dbt/README.md` (MANUAL ≈ README quick start; unique bits: explicit `dbt deps && dbt seed`
  step and the 'skip steps 3–4 if data already loaded' note)". No repo file changes for this.
- `Dagster/README.md`, `Dagster/scripts/README.md`: unchanged (links point to `../dbt/README.md`, still valid).

## 4. Git
Branch `docs/merge-manual-config` from `main` in the current directory (no worktree). The tree already has unrelated
uncommitted work (`tests/` moves, `.claude/.tmp`, `.gitignore`, `dbt/scripts/doctor.py`); stage **only my paths** so
it is not swept into these commits. Conventional commits, three small ones:
`refactor: move env templates and requirements to dbt/config`, `refactor: move script constants to scripts/settings.yml`,
`docs: slim root README, point dbt docs at config/`. Push / PR only after confirmation.

## Verification
1. `grep -rn '\.\./\.env\|[^/]requirements.txt\|dbt/\.env' --include='*.md' --include='*.py' --include=Makefile .` → no stale refs (`MANUAL` links are expected to remain).
2. `cd dbt && make help` works; `uv pip install --dry-run -r config/requirements.txt` resolves (Makefile `setup` path).
3. `cd dbt && .venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import envload, os; envload.load_env(); print(os.environ['HW_DBT_PROJECT_DIR'])"` prints the value from `config/.env`.
4. `.venv/bin/python scripts/doctor.py` — env vars section still shows values (see caveat below on the control_figures line).
5. `.venv/bin/python scripts/wizard.py --help` (import check only; not run non-interactively, it would rewrite the user's `.env`).
5b. settings: `check_hw.py --no-run --no-gh --json` and `check_db_from_profile.py --json` output identical to the pre-change baseline;
   `python3 ~/.ai/skills/_scripts/utils/find_hardcoded_scalars.py <script> --exit-nonzero-on-find` clean for each migrated script;
   loader self-check: `settings.section("nope")` and a missing key both raise `ValueError` naming key + `settings.yml`.
6. Relative links in the three edited READMEs resolve (`check-md-refs` skill or manual `ls`).

## Caveats to report
- `dbt/scripts/doctor.py` has uncommitted edits that are not mine (`RO0T`, `cf = RO0T` overriding `CONTROL_FIGURES_JSON`,
  a `##?` line): the "control_figures.json" check currently tests the repo root, so it will likely report a failure unrelated to this change. Left untouched.
- Pre-existing wording mismatch: `.env.example` and root README say paths are "relative to the repo root", the code resolves them from `dbt/`. Not changed here.
