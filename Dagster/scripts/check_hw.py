#!/usr/bin/env python3
"""Автопроверка ДЗ «Оркестрация в Dagster (Olist)»: 10 критериев по 1 баллу, от простых к сложным.

Что делает:
  1) через inspect_defs.py (интерпретатором проекта студента) описывает граф: ассеты, checks, расписания;
  2) (если нет --no-run) запускает `dagster asset materialize -m <модуль> --select '*'` в изолированном DAGSTER_HOME;
  3) читает итоги запуска (материализации, результаты checks) и сверяет DuckDB с эталоном Olist
     (сырые таблицы — raw_expectations.json, витрины — control_figures.json; файлы общие с ДЗ по dbt);
  4) через GitHub API проверяет, что PR создан и заполнен;
  5) печатает отчёт и итог «N из 10 баллов».

Каждый критерий состоит из подпроверок; балл дают, только если все они пройдены. Баллы независимы.
Соответствие уровням ДЗ: 1–7 баллов — «6–7», 8–9 — «8–9», 10 — «10». Критерии 7–10 пока без проверок
(см. Dagster/PLAN.md, этапы 4 и 6): набрать сейчас можно не больше 6 баллов.

Пути — из config/.env / .env.local (см. config/.env.example). Код возврата: 0 — набрано ≥ --min баллов, 2 — ошибка запуска.

    python scripts/check_hw.py                 # полный прогон
    python scripts/check_hw.py --no-run        # без запуска: граф + уже загруженные данные в DuckDB
    python scripts/check_hw.py --no-gh         # без обращения к GitHub (критерий 6 не будет пройден)
    python scripts/check_hw.py --json          # отчёт в JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "dbt" / "scripts"))      # общие модули: settings, envload, criteria, olist_data, gh_api…
import settings  # noqa: E402

settings.use(Path(__file__).with_name("settings.yml"))
settings.use_from_argv(sys.argv)                              # --settings <файл> подменяет настройки (тесты, другой проект)
ROOT = settings.root()

import olist_data  # noqa: E402
from criteria import Criterion, points, print_report, report_json  # noqa: E402
from envload import load_env  # noqa: E402
from utils import resolve_path  # noqa: E402

load_env(ROOT / "config")
S = settings.section("check_hw")
T, G, RD = S["thresholds"], S["graph"], S["readme"]
RULES = olist_data.MartRules(S["tolerance"]["rel"], S["tolerance"]["abs"], S["segment_values"], 2)
INSPECT = ROOT / "scripts" / "inspect_defs.py"


@dataclass
class Ctx:
    """Всё, что нужно для оценки; собирается в main(), в тестах задаётся напрямую."""
    project: Path
    info: dict = field(default_factory=dict)         # вывод inspect_defs --module
    events: dict = field(default_factory=dict)       # вывод inspect_defs --events (пусто, если запуска не было)
    run_rc: int | None = None                        # код возврата `dagster asset materialize`
    raw: tuple = field(default_factory=lambda: ([], 0, 0))   # olist_data.check_raw
    marts: dict = field(default_factory=dict)        # olist_data.check_marts
    readme: Path | None = None
    gh: dict | None = None

    @property
    def assets(self) -> list[dict]:
        return self.info.get("assets", [])

    @property
    def dbt_assets(self) -> list[dict]:
        return [a for a in self.assets if G["dbt_kind"] in a["kinds"]]

    @property
    def roots(self) -> list[dict]:
        return [a for a in self.assets if not a["parents"] and not a["external"]]

    @property
    def staging(self) -> list[dict]:
        return [a for a in self.dbt_assets if re.search(G["staging_regex"], a["key"])]

    @property
    def marts_assets(self) -> list[dict]:
        """dbt-ассеты, не staging и не корни графа (seeds): витрины."""
        stg = {a["key"] for a in self.staging}
        return [a for a in self.dbt_assets if a["parents"] and a["key"] not in stg]


def evaluate(ctx: Ctx) -> list[Criterion]:
    info, ev = ctx.info, ctx.events
    cs: list[Criterion] = []

    def new() -> Criterion:
        c = Criterion(len(cs) + 1, S["criteria_titles"][len(cs)])
        cs.append(c)
        return c

    # 1 — определения грузятся
    c = new()
    c.add(bool(info.get("ok")), "inspect_defs: Definitions загружаются без ошибок", info.get("error", "") if not info.get("ok") else "")
    c.add(len(ctx.assets) >= T["min_assets"], f"в графе ≥ {T['min_assets']} ассета", f"найдено: {len(ctx.assets)}")

    # 2 — raw-слой
    c = new()
    c.add(bool(ctx.roots), "есть raw-ассеты (корни графа)", f"корней: {len(ctx.roots)}")
    raw_res, raw_found, raw_total = ctx.raw
    bad_raw = [f"{k}: {d}" for k, ok, d in raw_res if not ok]
    c.add(bool(raw_res) and not bad_raw, f"исходные данные загружены полно ({raw_found} из {raw_total} таблиц, строки и суммы сверены)",
          "\n".join(bad_raw) if bad_raw else ("нет данных для сверки" if not raw_res else ""))

    # 3 — dbt в графе
    c = new()
    mk = ctx.marts_assets
    c.add(bool(ctx.dbt_assets), f"dbt-модели — ассеты Dagster (kind «{G['dbt_kind']}»)", f"dbt-ассетов: {len(ctx.dbt_assets)}")
    c.add(len(ctx.staging) >= T["staging_min"], f"≥ {T['staging_min']} staging-ассет (ключ по /{G['staging_regex']}/)",
          f"найдено: {[a['key'] for a in ctx.staging] or '—'}")
    c.add(len(mk) >= T["marts_min"], f"≥ {T['marts_min']} витрины в графе", f"найдено: {[a['key'] for a in mk] or '—'}")
    ext = [a["key"] for a in ctx.assets if a["external"]]
    c.add(bool(ctx.assets) and not ext, "lineage без разрывов: внешних (не материализуемых) ассетов нет",
          f"внешние ассеты (источники без связи с raw): {ext}" if ext else "")
    orphan = [a["key"] for a in [*ctx.staging, *mk] if not a["parents"]]
    c.add(bool(ctx.staging) and not orphan, "у каждого staging и каждой витрины есть upstream", f"без upstream: {orphan or '—'}")

    # 4 — dbt-тесты как checks
    c = new()
    dbt_keys = {a["key"] for a in ctx.dbt_assets}
    dbt_checks = [k for k in info.get("checks", []) if k["asset"] in dbt_keys]
    c.add(len(dbt_checks) >= T["min_checks"], f"у dbt-ассетов ≥ {T['min_checks']} asset check (dbt-тесты)", f"найдено checks: {len(dbt_checks)}")
    run_checks = ev.get("checks", [])
    failed = [f"{k['asset']}.{k['name']}" for k in run_checks if not k["passed"]]
    c.add(bool(run_checks) and not failed, f"все asset checks после запуска зелёные ({len(run_checks)} шт.)",
          ("не пройдены: " + ", ".join(failed[:8])) if failed else ("нет результатов запуска (запустите без --no-run)" if not run_checks else ""))
    n_pass = sum(1 for v in ctx.marts.values() if v["present"] and v["columns_ok"] and v["assert_ok"])
    n_present = sum(1 for v in ctx.marts.values() if v["present"])
    lines = [f"витрин в проекте: {n_present}, прошли контракт и сверку: {n_pass}, нужно ≥ {T['marts_match']}"]
    lines += [f"  · {n}: " + "; ".join(v["problems"][:3]) for n, v in ctx.marts.items() if v["present"] and v["problems"]]
    c.add(n_pass >= T["marts_match"], f"≥ {T['marts_match']} витрины: колонки по контракту и цифры в допуске", "\n".join(lines))

    # 5 — расписание и запуск
    c = new()
    daily = [s for s in info.get("schedules", []) if re.search(G["daily_cron_regex"], str(s["cron"]))]
    c.add(bool(daily), "есть ежедневное расписание (cron: минуты часы * * *)",
          f"расписания: {[(s['name'], s['cron']) for s in info.get('schedules', [])] or '—'}")
    mart_keys = {a["key"] for a in mk}
    covers = [s["name"] for s in daily if mart_keys and mart_keys <= set(s["asset_keys"])]
    c.add(bool(covers), "расписание запускает джоб, в который входят все витрины", f"подходят: {covers or '—'}")
    runs = ev.get("runs", [])
    run_ok = ctx.run_rc == 0 and bool(runs) and all(r["status"] == "SUCCESS" for r in runs)
    c.add(run_ok, "запуск из командной строки (`dagster asset materialize`) успешен",
          f"rc={ctx.run_rc}; запуски: {[r['status'] for r in runs] or '—'}" if not run_ok else "")

    # 6 — документация и PR
    c = new()
    if ctx.readme:
        txt = ctx.readme.read_text(encoding="utf-8", errors="ignore")
        c.add(bool(re.search(RD["install_regex"], txt)) and bool(re.search(RD["run_regex"], txt)),
              "README описывает установку и запуск", str(ctx.readme))
    else:
        c.add(False, "README найден", f"искал {', '.join(RD['names'])}")
    gh = ctx.gh
    if gh is None:
        c.add(False, "проверка GitHub отключена (--no-gh)", "запустите без --no-gh")
    elif gh.get("error"):
        c.add(False, "GitHub API доступен", gh["error"])
    elif not gh.get("pr"):
        c.add(False, "PR найден", f"в {gh['repo']} PR не найден (создайте PR или задайте HW_GH_PR)")
    else:
        pr = gh["pr"]
        c.add(True, f"PR найден: #{pr['number']} ({pr['state']}{', merged' if pr['merged'] else ''})", pr["url"])
        c.add(len(pr["title"].strip()) >= T["pr_title_len"], "у PR есть заголовок", pr["title"][:80])
        c.add(pr["body_len"] >= T["pr_body_len"], "описание PR заполнено", f"{pr['body_len']} знаков осмысленного текста (нужно ≥ {T['pr_body_len']})")
        c.add(pr["has_versions"], "в описании PR указаны версии dagster / dagster-dbt / dbt-core / адаптера", "формат: dagster-dbt 0.29.26")
        c.add(pr["has_image"], "в описании PR есть скриншот (lineage или успешный запуск)", "приложите картинку")

    # 7–10 — пока без проверок
    while len(cs) < len(S["criteria_titles"]):
        new().note("info", S["not_implemented_text"])
    return cs


def level_name(pts: int) -> str:
    return next((lv["name"] for lv in S["levels"] if pts >= lv["min_points"]), S["below_levels_name"])


# ----------------------------------------------------------------------------------------------
# Сбор данных
# ----------------------------------------------------------------------------------------------
def project_python(project: Path) -> str:
    """Интерпретатор проекта студента: HW_DAGSTER_PYTHON, иначе venv проекта из settings, иначе текущий."""
    if os.environ.get("HW_DAGSTER_PYTHON"):
        return str(resolve_path(os.environ["HW_DAGSTER_PYTHON"], ROOT))
    for rel in S["python_search"]:
        if (project / rel).exists():
            return str(project / rel)
    return sys.executable


def child_env(project: Path, db: Path, py: str, home: str | None = None) -> dict:
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([str(Path(py).parent), env["PATH"]])    # как активация venv: dagster-dbt ищет `dbt` в PATH
    env["OLIST_DUCKDB_PATH"] = str(db)
    env["PYTHONPATH"] = os.pathsep.join([*[str(project / p) for p in settings.section("inspect_defs")["pythonpath"]], env.get("PYTHONPATH", "")])
    if home:
        env["DAGSTER_HOME"] = home
    return env


def run_json(cmd: list[str], project: Path, env: dict, timeout: int) -> dict:
    try:
        r = subprocess.run(cmd, cwd=project, env=env, capture_output=True, text=True, timeout=timeout)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"таймаут {timeout} с"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}


def find_readme(project: Path) -> Path | None:
    for d in [project, *list(project.parents)[:S["search_parents"]]]:
        for n in RD["names"]:
            if (d / n).exists():
                return d / n
    return None


def hint_for(text: str, hints: list[dict]) -> dict | None:
    return next((h for h in hints if re.search(h["match"], text)), None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--settings", help="settings.yml проекта (по умолчанию — этого Dagster/)")
    ap.add_argument("--no-run", action="store_true", help="не запускать материализацию: граф и уже загруженные данные")
    ap.add_argument("--no-gh", action="store_true", help="не обращаться к GitHub API (критерий 6 не будет пройден)")
    ap.add_argument("--json", action="store_true", help="отчёт в JSON")
    ap.add_argument("--min", type=int, default=S["default_min_points"], help="минимальный балл для кода возврата 0")
    a = ap.parse_args()

    def need(name: str) -> str:
        if not os.environ.get(name):
            sys.exit(f"не задана переменная {name}: заполните {ROOT / 'config' / '.env'} (шаблон — .env.example)")
        return os.environ[name]

    project = resolve_path(need("HW_DAGSTER_PROJECT_DIR"), ROOT).resolve()
    module, db = need("HW_DAGSTER_MODULE"), resolve_path(need("OLIST_DUCKDB_PATH"), ROOT).resolve()
    if not project.is_dir():
        print(f"❌ нет каталога проекта {project}", file=sys.stderr)
        return 2
    py, log, to = project_python(project), (sys.stderr if a.json else sys.stdout), S["timeouts_s"]
    ctx = Ctx(project)

    print("🔎 Описываю граф Dagster…", file=log, flush=True)
    attrs = [x for n in settings.section("inspect_defs")["attrs"] for x in ("--attr", n)]
    ctx.info = run_json([py, str(INSPECT), "--module", module, *attrs], project, child_env(project, db, py), to["inspect"])

    home = os.environ.get("HW_DAGSTER_HOME") if a.no_run else tempfile.mkdtemp(prefix="hw-dagster-")
    if not a.no_run and ctx.info.get("ok"):
        cmd = [py, *[x.replace("{module}", module) for x in S["commands"]["materialize"]]]
        print("🚀 Материализую граф:", " ".join(cmd[1:]), file=log, flush=True)
        try:
            ctx.run_rc = subprocess.call(cmd, cwd=project, env=child_env(project, db, py, home), stdout=sys.stderr, stderr=sys.stderr, timeout=to["materialize"])
        except subprocess.TimeoutExpired:
            ctx.run_rc = 124
    if home and Path(home).is_dir():
        ctx.events = run_json([py, str(INSPECT), "--events", home], project, child_env(project, db, py, home), to["inspect"])

    shared = ROOT / S["shared_data_dir"]
    exp = json.loads((shared / S["data_files"]["raw_expectations"]).read_text(encoding="utf-8"))
    ctx.raw = olist_data.check_raw(db, exp)
    cf = json.loads((shared / S["data_files"]["control_figures"]).read_text(encoding="utf-8"))
    contract = json.loads((shared / S["data_files"]["marts_contract"]).read_text(encoding="utf-8"))
    ctx.marts = olist_data.check_marts(db, S["marts"], {x["key"] for x in ctx.dbt_assets}, contract, cf, RULES)
    ctx.readme = find_readme(project)
    if not a.no_gh:
        import gh_api

        print("🐙 Проверяю PR через GitHub API…", file=log, flush=True)
        ctx.gh = gh_api.pr_report(project)

    criteria = evaluate(ctx)
    pts = points(criteria)
    hints = yaml.safe_load((ROOT / "data" / S["hints_file"]).read_text(encoding="utf-8"))
    if a.json:
        print(report_json(criteria, max_points=len(criteria), level=level_name(pts), project=project))
    else:
        print_report(criteria, title="ДЗ Dagster (Olist)", project=project, level=level_name(pts), max_points=len(criteria),
                     hint_for=lambda t: hint_for(t, hints), detail_ok_prefixes=("≥", "PR найден"))
    return 0 if pts >= a.min else 1


if __name__ == "__main__":
    raise SystemExit(main())
