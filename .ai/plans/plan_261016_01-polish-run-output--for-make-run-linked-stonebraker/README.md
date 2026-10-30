# Polish `make run` output (wizard / doctor / check_db)

## Context
User wants clearer `make run` (setup → wizard → seeds → ready → check) output: repo URL, resolved PR, DB-labelled prompts, absolute paths, no doubled path, colored FAIL lines, and a useful message instead of bare `make: *** [ready] Error 1`.
All code in `dbt/scripts/`; constants go to `scripts/settings.yml` (strict loader `settings.py`).

## Changes
1. **Repo URL** — `wizard.py` step_github (~l.67-68): after repo is chosen print `   🔗 https://github.com/{repo}` (URL template → `settings.yml: gh_api.repo_url`).
2. **Found PR on empty answer** — after `wizard.py:71`: if `pr` empty and token+repo present, call `gh_api.find_pr(repo, token, project)` in try/except; print `   ✅ PR #{n}: {title} — {url}` or `   ⚠️ PR не найден: <err>`. Keep writing `HW_GH_PR=` empty (resolution stays dynamic).
3. **DB label prefix** — `wizard.py` step_db l.131-135: `lbl = S["db_labels"][kind]` (new `wizard.db_labels: {postgres: Postgres, clickhouse: ClickHouse}`), prompts become `f"{lbl}: Хост"` etc. (incl. port, user, db, password). Choice question unchanged.
4. **"Будет записано"** — `wizard.py:183-187`: group by file: `📝 Будет записано в {ENV_DIR/'.env'}:` then `   KEY=val`; then `📝 Будет записано в {ENV_DIR/'.env.local'}:` then `   KEY=******`.
5. **Готово** — `wizard.py:197`: use absolute `ENV_DIR/".env"` / `".env.local"` paths.
6. **Doubled path** — `doctor.py:50,54`: delete `cf = RO0T` override and debug label; restore `line(cf exists, "control_figures.json", str(cf))` → prints the path once and actually checks the file.
7. **Colored FAIL** — `logger.py`: add tiny `paint(text, ok)` (ANSI red/green only if `sys.stdout.isatty()` and no `NO_COLOR`); `Checks.line` and `target_line` prefix FAIL with `❌` and paint red, OK with `✅`. Unify `[OK  ]` width in `target_line`. Update `tests/test_logger.py` asserts (tests run non-tty → no ANSI, only emoji added).
8. **ready Error 1 detail** — `doctor.py` end: list failed checks with label + detail and a hint per failure (`make setup` / `make wizard` / `make seeds`), replace stale `just doctor` with `make ready`. `check_db_from_profile.py`: on failure print summary `❌ N target(ов) недоступны: … → проверьте profiles.yml / make wizard`. Makefile `ready`: run both scripts even if first fails (`doctor; d=$$?; check_db; c=$$?; [ $$d -eq 0 -a $$c -eq 0 ] || { echo "❌ ready: …см. выше"; exit 1; }`) so user sees all diagnostics at once.

## Not doing
No gh repo view, no colors in check_hw.py beyond shared logger, `pre` dead-code left (backlog note).

## Verification
- `make test` (pytest, updated test_logger + new small test for paint no-tty).
- `make run` with `WIZARD_ARGS=-ni` and with a missing clickhouse target: check each listed line visually.
- Work on branch `fix/run-output` from current branch; commit, ask before push (dataengy/beloz978 account per remote).
