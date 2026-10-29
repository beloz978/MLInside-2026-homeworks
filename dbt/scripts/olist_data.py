"""Сверка данных Olist в DuckDB с эталоном: сырые таблицы (raw_expectations.json) и витрины (control_figures.json).

Общий код для автопроверок dbt/ и Dagster/: пути, допуски и списки приходят параметрами из settings.yml вызывающего."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from db import table_ref
from utils import close


@dataclass(frozen=True)
class MartRules:
    rel_tol: float
    abs_tol: float
    segment_values: list[str]
    min_segment_values: int


def check_raw(db: Path, exp: dict) -> tuple[list[tuple[str, bool, str]], int, int]:
    """Полнота исходных данных в DuckDB: таблицы, число строк, колонки, контрольные суммы.
    Возвращает ([(таблица, ok, детали)], найдено_таблиц, всего_нужно)."""
    import duckdb

    tol = exp["tolerance"]
    res: list[tuple[str, bool, str]] = []
    if not db.exists():
        return [(k, False, f"нет файла БД {db}") for k in exp["required"]], 0, len(exp["required"])
    con = duckdb.connect(str(db), read_only=True)
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


def mart_assertions(name: str, cf: dict, q, rules: MartRules) -> list[tuple[str, bool, str]]:
    """Возвращает [(описание, ok, детали)]. q(sql) -> первое значение."""
    g = cf["global"]
    res: list[tuple[str, bool, str]] = []

    def eq(desc, got, exp, rel=rules.rel_tol, abs_=0.0):
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
           top["late_rate_pct"], 0, rules.abs_tol)
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
        res.append(("segment ⊂ {HIGH,MEDIUM,LOW}, >=2 значений", seg <= set(rules.segment_values) and len(seg) >= rules.min_segment_values,
                    f"значения: {sorted(map(str, seg))}"))
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


def check_marts(db: Path, names: list[str], present: set[str], contract: dict, cf: dict, rules: MartRules) -> dict[str, dict]:
    """Для каждой витрины из `names`: присутствует ли (`present` — имена моделей проекта), есть ли колонки, сходятся ли цифры."""
    import duckdb

    out: dict[str, dict] = {}
    con = duckdb.connect(str(db), read_only=True) if db.exists() else None
    for name in names:
        info = {"present": name in present, "columns_ok": False, "assert_ok": False, "problems": []}
        out[name] = info
        if not info["present"]:
            continue
        if con is None:
            info["problems"].append(f"нет файла БД {db}")
            continue
        t = table_ref(con, name)
        if not t:
            info["problems"].append("таблицы нет в DuckDB (dbt build не создал?)")
            continue
        cols = {r[0].lower() for r in con.execute(f"select * from {t} limit 0").description}
        need = [c.lower() for c in contract[name]["columns"]]
        miss = [c for c in need if c not in cols]
        info["columns_ok"] = not miss
        if miss:
            info["problems"].append(f"нет колонок: {', '.join(miss)}")
            continue

        def q(sql, all_=False, _t=t):
            cur = con.execute(sql.replace("{t}", _t))
            return cur.fetchall() if all_ else cur.fetchone()[0]

        try:
            results = mart_assertions(name, cf, q, rules)
        except Exception as e:  # noqa: BLE001
            info["problems"].append(f"ошибка сверки: {type(e).__name__}: {str(e)[:120]}")
            continue
        bad = [f"{d} ({det})" for d, ok, det in results if not ok]
        info["assert_ok"] = not bad
        info["problems"] += bad
    return out
