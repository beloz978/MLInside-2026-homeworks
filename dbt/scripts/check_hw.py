#!/usr/bin/env python3
"""Автопроверка ДЗ «Введение в dbt (Olist)»: 10 критериев по 1 баллу, от простых к сложным.

Что делает:
  1) (если нет --no-run) поднимает raw-слой, запускает dbt deps → build → docs generate;
  2) собирает проект на втором таргете (Postgres/ClickHouse), если он описан в profiles.yml и доступен;
  3) разбирает manifest.json / run_results.json и файлы проекта;
  4) сверяет витрины с эталоном data/control_figures.json (контракт колонок — data/marts_contract.json);
  5) через GitHub API проверяет, что PR создан и заполнен, и смотрит статус CI (GitHub Actions);
  6) печатает отчёт по критериям и итог «N из 10 баллов».

Каждый критерий состоит из подпроверок; балл дают, только если все подпроверки критерия пройдены.
Баллы независимы: проваленный критерий не отнимает баллы у остальных.
Соответствие уровням ДЗ: 1–7 баллов — «6–7», 8–9 — «8–9», 10 — «10».

Пути берутся из .env / .env.local (см. `just wizard`). Код возврата: 0 — набрано ≥ --min баллов
(по умолчанию 1), 2 — ошибка запуска.

    python scripts/check_hw.py                 # полный прогон
    python scripts/check_hw.py --no-run        # по уже собранным artefacts target/
    python scripts/check_hw.py --no-gh         # без обращения к GitHub
    python scripts/check_hw.py --json          # отчёт в JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import load_env  # noqa: E402
from settings import section  # noqa: E402

load_env()
S = section("check_hw")
T = S["thresholds"]

MARTS, QA_PACKAGES, ORDER_HOOKS = S["marts"], S["qa_packages"], S["order_hooks"]
REL_TOL, ABS_TOL = S["tolerance"]["rel"], S["tolerance"]["abs"]
HINTS = yaml.safe_load((ROOT / "data" / S["data_files"]["hints"]).read_text(encoding="utf-8"))
EMO = {"ok": "✅", "fail": "❌", "warn": "⚠️ ", "info": "🆗"}


@dataclass
class Sub:
    status: str  # ok | fail | warn | info  (warn/info баллов не влияют)
    text: str
    detail: str = ""


@dataclass
class Criterion:
    n: int
    title: str
    subs: list[Sub] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return any(s.status == "ok" for s in self.subs) and not any(s.status == "fail" for s in self.subs)

    def add(self, ok: bool, text: str, detail: str = "") -> None:
        self.subs.append(Sub("ok" if ok else "fail", text, detail))

    def note(self, status: str, text: str, detail: str = "") -> None:
        self.subs.append(Sub(status, text, detail))


class Ctx:
    def __init__(self, project: Path, profiles: Path, db: Path, cf: dict, contract: dict):
        self.project, self.profiles, self.db, self.cf, self.contract = project, profiles, db, cf, contract
        self.cfg = yaml.safe_load((project / "dbt_project.yml").read_text(encoding="utf-8"))
        self.pname = self.cfg["name"]
        self.manifest: dict = {}
        self.build_rc: int | None = None
        self.docs_rc: int | None = None
        self.deps_rc: int | None = None
        self.second: dict = {}  # {target, reachable, msg, build_rc}


    def search_dirs(self) -> list[Path]:
        """Где искать файлы уровня репозитория: каталог проекта и до 2 родителей."""
        p = self.project
        return [p, *list(p.parents)[:S["search_parents"]]]

    def find_file(self, names: list[str]) -> Path | None:
        for d in self.search_dirs():
            for n in names:
                if (d / n).exists():
                    return d / n
        return None

    def nodes(self, rtype: str, own_only: bool = True) -> list[dict]:
        out = []
        for n in self.manifest.get("nodes", {}).values():
            if n.get("resource_type") == rtype and (not own_only or n.get("package_name") == self.pname):
                out.append(n)
        return out

    def packages_declared(self) -> list[str]:
        f = self.project / "packages.yml"
        if not f.exists():
            return []
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        names = []
        for p in data.get("packages", []):
            names.append(str(p.get("package") or p.get("git") or p.get("local") or "").lower().replace("-", "_"))
        return names

    def packages_installed(self) -> set[str]:
        return {m.get("package_name") for m in self.manifest.get("macros", {}).values()} | \
               {n.get("package_name") for n in self.manifest.get("nodes", {}).values()}



# ----------------------------------------------------------------------------------------------
# Запуск dbt
# ----------------------------------------------------------------------------------------------
def run_dbt(ctx: Ctx, args: list[str], target: str | None = None) -> int:
    # -c вместо -m dbt.cli.main: иначе runpy печатает RuntimeWarning («found in sys.modules»)
    cmd = [sys.executable, "-c", "from dbt.cli.main import cli; cli()", *args, "--profiles-dir", str(ctx.profiles)]
    if target:
        cmd += ["--target", target]
    print("\n$ dbt", " ".join(cmd[3:]), flush=True)
    env = os.environ.copy()
    env["OLIST_DUCKDB_PATH"] = str(ctx.db)
    return subprocess.call(cmd, cwd=ctx.project, env=env, stdout=sys.stderr, stderr=sys.stderr)


def hint_for(text: str) -> dict | None:
    """Подсказка (hint + необязательный url) к подпроверке: первое совпадение регэкспа из data/hints.yaml."""
    return next((h for h in HINTS if re.search(h["match"], text)), None)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def pipeline(ctx: Ctx, second_target: str | None) -> None:
    ctx.db.parent.mkdir(parents=True, exist_ok=True)
    ctx.deps_rc = run_dbt(ctx, ["deps"])
    seed_rc = 0
    if any((ctx.project / "seeds").glob("*.csv")):      # source() не знает про seed: грузим данные до build
        seed_rc = run_dbt(ctx, ["seed"]) if ctx.deps_rc == 0 else 1
    ctx.build_rc = run_dbt(ctx, ["build"]) if ctx.deps_rc == 0 and seed_rc == 0 else 1
    ctx.docs_rc = run_dbt(ctx, ["docs", "generate"]) if ctx.deps_rc == 0 else 1
    ctx.manifest = read_json(ctx.project / "target" / "manifest.json")
    if second_target:
        check_second_target(ctx, second_target)


def check_second_target(ctx: Ctx, second_target: str) -> None:
    """Доступность СУБД второго таргета и сборка на нём (seed, если есть seeds/, затем build)."""
    sc = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_db_from_profile.py"),
                         "--profiles-dir", str(ctx.profiles), "--targets", second_target, "--json"],
                        capture_output=True, text=True, env=os.environ.copy())
    try:
        r = json.loads(sc.stdout)["results"][0]
    except Exception:  # noqa: BLE001
        r = {"ok": False, "message": (sc.stdout + sc.stderr)[:200]}
    ctx.second = {"target": second_target, "reachable": r["ok"], "msg": r["message"], "build_rc": None}
    if r["ok"]:
        has_seeds = any((ctx.project / "seeds").glob("*.csv"))
        skip_seed = os.environ.get("HW_SKIP_SECOND_SEED") == "1"   # данные уже загружены в эту БД
        seed_rc = run_dbt(ctx, ["seed"], target=second_target) if has_seeds and not skip_seed else 0
        ctx.second["build_rc"] = run_dbt(ctx, ["build"], target=second_target) if seed_rc == 0 else seed_rc
        ctx.manifest = read_json(ctx.project / "target" / "manifest.json")


# ----------------------------------------------------------------------------------------------
# Сверка витрин с эталоном
# ----------------------------------------------------------------------------------------------
def close(a, b, rel=REL_TOL, abs_=0.0) -> bool:
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= max(abs_, rel * abs(float(b)))


def table_ref(con, name: str) -> str | None:
    r = con.execute("select table_schema from information_schema.tables where lower(table_name)=? "
                    "and table_schema not in ('information_schema','raw') order by (table_schema='main') desc limit 1",
                    [name]).fetchone()
    return f'"{r[0]}"."{name}"' if r else None


def mart_assertions(name: str, cf: dict, q) -> list[tuple[str, bool, str]]:
    """Возвращает [(описание, ok, детали)]. q(sql) -> первое значение."""
    g = cf["global"]
    res: list[tuple[str, bool, str]] = []

    def eq(desc, got, exp, rel=REL_TOL, abs_=0.0):
        res.append((desc, close(got, exp, rel, abs_), f"получено {got}, ожидалось {exp}"))

    if name == "mart_daily_state_metrics":
        m = cf[name]
        eq("sum(orders_cnt) = заказы с позициями", q("select sum(orders_cnt) from {t}"), g["orders_with_items"], 0)
        eq("sum(gmv) = GMV", q("select sum(gmv) from {t}"), g["gmv"])
        for r in m["orders_by_state_top"][:3]:
            eq(f"заказы {r['state']}", q(f"select sum(orders_cnt) from {{t}} where customer_state='{r['state']}'"), r["orders"], 0)
        eq("число строк (дата × штат)", q("select count(*) from {t}"), m["date_state_groups"], 0)
    elif name == "mart_delivery_by_state":
        m = cf[name]
        eq("sum(delivered_orders) = доставлено с датой", q("select sum(delivered_orders) from {t}"), m["delivered_known"], 0)
        eq("sum(late_orders) = опоздавшие", q("select sum(late_orders) from {t}"), m["late"], 0)
        top = m["top_late_rate_states"][0]
        eq(f"late_rate_pct {top['state']}", q(f"select max(late_rate_pct) from {{t}} where customer_state='{top['state']}'"),
           top["late_rate_pct"], 0, ABS_TOL)
    elif name == "mart_category_performance":
        m = cf[name]
        eq("sum(revenue) = GMV", q("select sum(revenue) from {t}"), g["gmv"])
        for r in m["top_by_revenue"][:2]:
            eq(f"revenue {r['category']}", q(f"select sum(revenue) from {{t}} where product_category='{r['category']}'"), r["revenue"])
    elif name == "mart_customer_profile":
        m = cf[name]
        eq("число клиентов", q("select count(*) from {t}"), m["customers"], 0)
        eq("sum(total_spent) = GMV", q("select sum(total_spent) from {t}"), g["gmv"])
        eq("max(orders_cnt)", q("select max(orders_cnt) from {t}"), m["max_orders_per_customer"], 0)
        eq("max(recency_days)", q("select max(recency_days) from {t}"), m["recency_days_quantiles"]["max"], 0, 1)
        seg = {r[0] for r in q("select distinct segment from {t}", all_=True)}
        res.append(("segment ⊂ {HIGH,MEDIUM,LOW}, >=2 значений", seg <= set(S["segment_values"]) and len(seg) >= T["min_segment_values"], f"значения: {sorted(map(str, seg))}"))
    elif name == "mart_hourly_order_pattern":
        m = cf[name]
        eq("sum(orders_cnt)", q("select sum(orders_cnt) from {t}"), g["orders_with_items"], 0)
        eq("число ячеек день×час", q("select count(*) from {t}"), m["dow_hour_cells"], 0)
        c = m["peak_dow_hour_cell"]
        eq(f"пик: день {c['dow']}, час {c['hour']}", q(f"select sum(orders_cnt) from {{t}} where day_of_week={c['dow']} and hour_of_day={c['hour']}"), c["orders"], 0)
        eq("заказы в 16:00", q("select sum(orders_cnt) from {t} where hour_of_day=16"), m["by_hour"]["16"], 0)
    elif name == "mart_seller_analytics":
        m = cf[name]
        eq("число продавцов", q("select count(*) from {t}"), m["sellers"], 0)
        eq("sum(revenue) = GMV", q("select sum(revenue) from {t}"), g["gmv"])
        t0 = m["top_by_revenue"][0]
        eq("revenue топ-продавца", q(f"select sum(revenue) from {{t}} where seller_id='{t0['seller_id']}'"), t0["revenue"])
    return res


def check_marts(ctx: Ctx) -> dict[str, dict]:
    """Для каждой витрины из контракта: присутствует ли, есть ли колонки, сходятся ли цифры."""
    import duckdb

    present = {n["name"] for n in ctx.nodes("model")}
    out: dict[str, dict] = {}
    con = duckdb.connect(str(ctx.db), read_only=True) if ctx.db.exists() else None
    for name in MARTS:
        info = {"present": name in present, "columns_ok": False, "assert_ok": False, "problems": []}
        out[name] = info
        if not info["present"]:
            continue
        if con is None:
            info["problems"].append(f"нет файла БД {ctx.db}")
            continue
        t = table_ref(con, name)
        if not t:
            info["problems"].append("таблицы нет в DuckDB (dbt build не создал?)")
            continue
        cols = {r[0].lower() for r in con.execute(f"select * from {t} limit 0").description}
        need = [c.lower() for c in ctx.contract[name]["columns"]]
        miss = [c for c in need if c not in cols]
        info["columns_ok"] = not miss
        if miss:
            info["problems"].append(f"нет колонок: {', '.join(miss)}")
            continue

        def q(sql, all_=False, _t=t):
            cur = con.execute(sql.replace("{t}", _t))
            return cur.fetchall() if all_ else cur.fetchone()[0]

        try:
            results = mart_assertions(name, ctx.cf, q)
        except Exception as e:  # noqa: BLE001
            info["problems"].append(f"ошибка сверки: {type(e).__name__}: {str(e)[:120]}")
            continue
        bad = [f"{d} ({det})" for d, ok, det in results if not ok]
        info["assert_ok"] = not bad
        info["problems"] += bad
    return out


# ----------------------------------------------------------------------------------------------
# Статические проверки
# ----------------------------------------------------------------------------------------------
def check_raw(ctx: Ctx) -> tuple[list[tuple[str, bool, str]], int, int]:
    """Полнота исходных данных в DuckDB: таблицы, число строк, колонки, контрольные суммы.
    Возвращает ([(таблица, ok, детали)], найдено_таблиц, всего_нужно)."""
    import duckdb

    exp = json.loads((ROOT / "data" / S["data_files"]["raw_expectations"]).read_text(encoding="utf-8"))
    tol = exp["tolerance"]
    res: list[tuple[str, bool, str]] = []
    if not ctx.db.exists():
        return [(k, False, f"нет файла БД {ctx.db}") for k in exp["required"]], 0, len(exp["required"])
    con = duckdb.connect(str(ctx.db), read_only=True)
    found = 0
    for key, e in exp["required"].items():
        r = con.execute("select table_schema, table_name from information_schema.tables where lower(table_name) in (%s) "
                        "and table_schema not in ('information_schema','pg_catalog') "
                        "order by table_type='VIEW', table_schema limit 1" % ",".join("?" * len(e["candidates"])),
                        e["candidates"]).fetchone()
        if not r:
            res.append((key, False, f"таблица не найдена (ищу: {', '.join(e['candidates'][:2])}…)"))
            continue
        found += 1
        t = f'"{r[0]}"."{r[1]}"'
        probs = []
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        if n != e["rows"]:
            probs.append(f"строк {n}, ожидалось {e['rows']}")
        cols = {c[0].lower() for c in con.execute(f"select * from {t} limit 0").description}
        miss = [c for c in e["columns"] if c not in cols]
        if miss:
            probs.append(f"нет колонок: {', '.join(miss)}")
        else:
            for a in e["aggregates"]:
                got = con.execute(f"select {a['sql']} from {t}").fetchone()[0]
                if got is None or abs(float(got) - a["expected"]) > max(0.5, tol * abs(a["expected"])):
                    probs.append(f"{a['name']} = {got}, ожидалось {a['expected']}")
        res.append((key, not probs, f"{r[0]}.{r[1]}: " + ("; ".join(probs) if probs else f"{n} строк, колонки и суммы в норме")))
    return res, found, len(exp["required"])


def tests_for(ctx: Ctx, model_unique_id: str) -> list[dict]:
    return [t for t in ctx.nodes("test") if model_unique_id in t.get("depends_on", {}).get("nodes", [])]


def test_kind(t: dict) -> str:
    md = t.get("test_metadata")
    return md["name"] if md else "singular"



def evaluate(ctx: Ctx, gh: dict | None) -> list[Criterion]:
    m = ctx.manifest
    marts = check_marts(ctx) if m else {}
    n_pass = sum(1 for v in marts.values() if v["present"] and v["columns_ok"] and v["assert_ok"])
    n_present = sum(1 for v in marts.values() if v["present"])
    own_models = ctx.nodes("model")
    declared, installed = ctx.packages_declared(), ctx.packages_installed()
    own_macros = [x for x in m.get("macros", {}).values() if x.get("package_name") == ctx.pname]
    used = {mid for n in list(m.get("nodes", {}).values()) for mid in n.get("depends_on", {}).get("macros", [])}
    used_pk = {mid.split(".")[1] for mid in used if mid.startswith("macro.")}
    singular = [t for t in ctx.nodes("test") if test_kind(t) == "singular"]

    def marts_detail(need: int) -> str:
        lines = [f"витрин в проекте: {n_present}, прошли контракт и сверку: {n_pass}, нужно ≥ {need}"]
        for n, v in marts.items():
            if v["present"] and v["problems"]:
                lines.append(f"  · {n}: " + "; ".join(v["problems"][:3]))
        return "\n".join(lines)

    cs: list[Criterion] = []

    def new(title: str) -> Criterion:
        c = Criterion(len(cs) + 1, title)
        cs.append(c)
        return c

    # 1 — проект собирается
    c = new("Проект собирается, данные загружены")
    c.add(ctx.deps_rc == 0, "dbt deps: пакеты установлены", f"rc={ctx.deps_rc}")
    c.add(ctx.build_rc == 0, "dbt seed + dbt build: данные, модели и тесты проходят", f"rc={ctx.build_rc}")
    raw_res, raw_found, raw_total = check_raw(ctx)
    seeds = [x for x in m.get("nodes", {}).values() if x.get("resource_type") == "seed" and x.get("package_name") == ctx.pname]
    c.note("info", f"источник данных: {len(seeds)} seed-файлов в проекте" if seeds else "источник данных: готовые таблицы (seed-файлов в проекте нет)")
    bad_raw = [f"{k}: {d}" for k, ok, d in raw_res if not ok]
    c.add(not bad_raw, f"исходные данные загружены полно ({raw_found} из {raw_total} таблиц, строки и суммы сверены)",
          "\n".join(bad_raw) + ("\nподсказка: `make seeds`, затем `dbt seed`" if bad_raw else ""))

    # 2 — документация
    c = new("Документация генерируется")
    c.add(ctx.docs_rc == 0, "dbt docs generate без ошибок", f"rc={ctx.docs_rc}")
    c.add((ctx.project / "target" / "catalog.json").exists(), "catalog.json создан")

    # 3 — описания
    c = new("Описания в schema.yml")
    undoc = [n["name"] for n in own_models if not (n.get("description") or "").strip()]
    nocol = [n["name"] for n in own_models if not any((x.get("description") or "").strip() for x in n.get("columns", {}).values())]
    c.add(bool(own_models) and not undoc, "у всех моделей есть description", f"без description: {undoc or '—'}")
    c.add(bool(own_models) and not nocol, "у всех моделей описаны ключевые колонки", f"без описанных колонок: {nocol or '—'}")

    # 4 — базовые тесты
    c = new("Базовые тесты данных")
    kinds = {test_kind(t) for t in ctx.nodes("test")}
    for k in ("not_null", "unique", "accepted_values", "relationships"):
        c.add(k in kinds, f"тест {k} используется")
    mart_nodes = [n for n in own_models if n["name"] in MARTS]
    nokey = [n["name"] for n in mart_nodes
             if not {test_kind(t) for t in tests_for(ctx, n["unique_id"])} & {"unique", "unique_combination_of_columns"}]
    c.add(bool(mart_nodes) and not nokey, "на каждой витрине есть тест уникальности ключа", f"без теста: {nokey or '—'}")

    # 5 — первые две витрины
    c = new("Две витрины сходятся с эталоном")
    c.add(n_pass >= T["marts_basic"], f"≥ {T['marts_basic']} витрины: колонки по контракту и цифры в допуске", marts_detail(T["marts_basic"]))

    # 6 — макрос и пакеты
    c = new("Свой макрос и пакеты")
    used_own = [x["name"] for x in own_macros if x["unique_id"] in used]
    c.add(bool(used_own), "свой макрос создан и используется в моделях", f"используются: {used_own or 'нет'}")
    for pk in ("dbt_utils", "dbt_date"):
        c.add(any(pk in d for d in declared) and pk in used_pk, f"пакет {pk} объявлен и используется",
              f"объявлен: {any(pk in d for d in declared)}, используется: {pk in used_pk}")

    # 7 — PR создан и заполнен (GitHub API)
    c = new("Pull request создан и заполнен (GitHub API)")
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
        if not pr["has_versions"]:
            c.note("warn", "в описании не видно версий dbt-core/адаптера", "желательно: dbt-core 1.x.y, dbt-duckdb 1.x.y")
        if not pr["has_image"]:
            c.note("warn", "в описании нет скриншота (DAG из dbt Docs)", "желательно приложить картинку")

    # 8 — расширенная проверка качества
    c = new("Витрины и тесты 8–9: 4 витрины, singular, unit")
    c.add(n_pass >= T["marts_extended"], f"≥ {T['marts_extended']} витрины сходятся с эталоном", marts_detail(T["marts_extended"]))
    c.add(len(singular) >= T["singular_tests"], f"≥ {T['singular_tests']} singular-теста", f"найдено: {len(singular)}")
    ut = [u for u in m.get("unit_tests", {}).values() if u.get("package_name") == ctx.pname]
    c.add(len(ut) >= T["unit_tests"], f"≥ {T['unit_tests']} unit-тест (dbt 1.8+)", f"найдено: {len(ut)}")

    # 9 — инженерная обвязка
    c = new("Инженерная обвязка 8–9: QA-пакеты, pre-commit, Makefile/justfile")
    qa = [p for p in QA_PACKAGES if any(p in d for d in declared) and p in installed]
    c.add(len(qa) >= T["qa_packages"], f"≥ {T['qa_packages']} QA-пакета из {QA_PACKAGES}", f"объявлены и установлены: {qa or '—'}")
    pc = ctx.find_file([".pre-commit-config.yaml"])
    if pc:
        txt = pc.read_text(encoding="utf-8").lower()
        c.add("sqlfluff" in txt, "pre-commit: sqlfluff")
        c.add(bool(re.search(r"dbt[ -]parse", txt)), "pre-commit: dbt parse")
        c.add(any(h in txt for h in ORDER_HOOKS), "pre-commit: хук проверки проекта", "/".join(ORDER_HOOKS))
    else:
        c.add(False, ".pre-commit-config.yaml найден")
    mk = ctx.find_file(["Makefile", "makefile", "justfile", "Justfile"])
    targets = re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", mk.read_text(encoding="utf-8"), flags=re.M) if mk else []
    c.add(bool(targets), "Makefile/justfile с целями", f"{mk or 'не найден'}; цели: {targets[:6] or '—'}")

    # 10 — максимум
    c = new("Максимум: 6 витрин, CI, evaluator, incremental/snapshot, портабельность, второй таргет")
    c.add(n_pass >= T["marts_all"], f"все {T['marts_all']} витрин сходятся с эталоном", marts_detail(T["marts_all"]))
    c.add(any("dbt_project_evaluator" in d for d in declared) and "dbt_project_evaluator" in installed, "dbt_project_evaluator установлен")
    snaps = ctx.nodes("snapshot")
    inc = [n["name"] for n in own_models if n.get("config", {}).get("materialized") == "incremental"]
    c.add(bool(snaps or inc), "incremental-модель или snapshot (SCD2)", f"incremental: {inc or '—'}; snapshots: {[s['name'] for s in snaps] or '—'}")
    portable = [x["name"] for x in own_macros if "adapter.dispatch" in (x.get("macro_sql") or "") or "target.type" in (x.get("macro_sql") or "")]
    c.add(bool(portable), "макрос портабельности (adapter.dispatch / target.type)", f"найдено: {portable or '—'}")
    ci_files = []
    for d in ctx.search_dirs():
        wf = d / ".github" / "workflows"
        if wf.exists():
            ci_files += [f for f in wf.glob("*.y*ml") if "dbt" in f.read_text(encoding="utf-8", errors="ignore").lower()]
    c.add(bool(ci_files), "GitHub Actions: workflow запускает dbt", f"{[f.name for f in ci_files] or '—'}")
    if gh and gh.get("pr") and gh.get("ci"):
        st, msg = gh["ci"]
        c.add(st == "success", "CI на коммите PR прошёл (GitHub API)", msg)
    else:
        c.add(False, "CI на коммите PR прошёл (GitHub API)", "PR или данные Actions недоступны")
    s = ctx.second
    if not s:
        c.add(False, "второй таргет (Postgres/ClickHouse) описан в profiles.yml", "нужен output типа postgres или clickhouse")
    else:
        c.add(bool(s["reachable"]), f"СУБД второго таргета «{s['target']}» доступна", s["msg"])
        c.add(s["build_rc"] == 0, f"dbt build --target {s['target']} проходит", f"rc={s['build_rc']}")
    return cs


def level_name(points: int) -> str:
    return next((lv["name"] for lv in S["levels"] if points >= lv["min_points"]), S["below_levels_name"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-run", action="store_true", help="не запускать dbt, использовать готовые target/ и DuckDB")
    ap.add_argument("--with-second", action="store_true", help="вместе с --no-run: всё же собрать проект на втором таргете")
    ap.add_argument("--no-gh", action="store_true", help="не обращаться к GitHub API (критерий 7 и CI будут не пройдены)")
    ap.add_argument("--json", action="store_true", help="отчёт в JSON")
    ap.add_argument("--min", type=int, default=S["default_min_points"], help="минимальный балл для кода возврата 0")
    ap.add_argument("--second-target", default=os.environ.get("HW_SECOND_TARGET") or None,
                    help="имя второго target (по умолчанию $HW_SECOND_TARGET или первый не-duckdb из profiles.yml)")
    a = ap.parse_args()

    def pth(name: str, default: str | None = None) -> Path:
        v = os.environ.get(name) or default
        if not v:
            sys.exit(f"не задана переменная {name} (запустите `just wizard`)")
        p = Path(v).expanduser()
        return (p if p.is_absolute() else ROOT / p).resolve()

    project = pth("HW_DBT_PROJECT_DIR")
    profiles = pth("HW_DBT_PROFILES_DIR", str(project))
    db = pth("OLIST_DUCKDB_PATH")
    if not (project / "dbt_project.yml").exists():
        print(f"❌ нет dbt_project.yml в {project}", file=sys.stderr)
        return 2
    cf = json.loads(pth("CONTROL_FIGURES_JSON", "data/control_figures.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "data" / S["data_files"]["marts_contract"]).read_text(encoding="utf-8"))
    ctx = Ctx(project, profiles, db, cf, contract)

    second = a.second_target
    if not second and (profiles / "profiles.yml").exists():
        prof = yaml.safe_load((profiles / "profiles.yml").read_text(encoding="utf-8")).get(ctx.cfg.get("profile"), {})
        for name, out in (prof.get("outputs") or {}).items():
            if out.get("type") in ("postgres", "clickhouse"):
                second = name
                break

    log = sys.stderr if a.json else sys.stdout
    if a.no_run:
        ctx.manifest = read_json(project / "target" / "manifest.json")
        ctx.deps_rc = 0 if (project / "dbt_packages").exists() or not ctx.packages_declared() else 1
        rr = read_json(project / "target" / "run_results.json")
        bad = [r for r in rr.get("results", []) if r.get("status") in ("error", "fail")]
        ctx.build_rc = 0 if rr.get("results") and not bad else 1
        ctx.docs_rc = 0 if (project / "target" / "catalog.json").exists() else 1
        if a.with_second and second:
            check_second_target(ctx, second)
        else:
            print("⚠️  --no-run: второй таргет не собирается, критерий 10 не может быть пройден (добавьте --with-second)", file=sys.stderr)
    else:
        print("🚀 Запускаю dbt…", file=log, flush=True)
        pipeline(ctx, second)
    if not ctx.manifest:
        print("❌ manifest.json не найден: проект не собрался (см. вывод dbt выше)", file=sys.stderr)

    gh = None
    if not a.no_gh:
        import gh_api

        print("🐙 Проверяю PR через GitHub API…", file=log, flush=True)
        gh = gh_api.pr_report(project)

    criteria = evaluate(ctx, gh)
    points = sum(c.passed for c in criteria)

    if a.json:
        print(json.dumps({"points": points, "max": 10, "level": level_name(points), "project": str(project),
                          "criteria": [{"n": c.n, "title": c.title, "passed": c.passed, "subs": [asdict(s) for s in c.subs]} for c in criteria]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"\n{'=' * 8} 📋 Отчёт: ДЗ dbt (Olist) {'=' * 8}\nПроект: {project}")
        for c in criteria:
            done = sum(s.status == "ok" for s in c.subs)
            total = sum(s.status in ("ok", "fail") for s in c.subs)
            print(f"\n{'🟢' if c.passed else '🔴'} Балл {c.n}/10 — {c.title}  [{done}/{total}]")
            for s in c.subs:
                print(f"   {EMO[s.status]} {s.text}")
                if s.detail and (s.status != "ok" or s.text.startswith(("≥", "PR найден"))):
                    for ln in s.detail.splitlines():
                        print(f"        {ln}")
                h = hint_for(s.text) if s.status in ("fail", "warn") else None
                if h:
                    print(f"        💡 {h['hint']}")
                    if h.get("url"):
                        print(f"        🔗 {h['url']}")
        bar = "".join("🟩" if c.passed else "⬜" for c in criteria)
        print(f"\n{'=' * 8} 🏁 Итог {'=' * 8}\n{bar}\n🎯 Проект прошёл на {points} из 10 баллов — уровень «{level_name(points)}»")
        miss = [f"{c.n}. {c.title}" for c in criteria if not c.passed]
        if miss:
            print("📌 Не хватает:")
            for m in miss:
                print(f"   • {m}")
    return 0 if points >= a.min else 1


if __name__ == "__main__":
    raise SystemExit(main())
