#!/usr/bin/env python3
"""Описание проекта Dagster студента в JSON. Запускается интерпретатором ПРОЕКТА студента (там стоит dagster),
поэтому использует только stdlib + dagster: ни PyYAML, ни настроек чекера — всё приходит аргументами.

  python inspect_defs.py --module olist_dagster.definitions --attr defs     # граф, checks, расписания, сенсоры
  python inspect_defs.py --events <DAGSTER_HOME>                            # итоги запусков из инстанса

Всегда печатает один JSON-объект. Ошибка загрузки → {"ok": false, "error": "..."}, код возврата 1."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
import traceback
import warnings


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:  # noqa: BLE001 — публичные атрибуты разных версий Dagster бросают по-разному
        return default


def resolve_defs(mod, attrs: list[str]):
    """Definitions из модуля: переменная `defs`, либо @definitions-функция (LazyDefinitions), либо любая Definitions."""
    import dagster as dg

    names = [*attrs, *[a for a in dir(mod) if not a.startswith("_") and a not in attrs]]
    for n in names:
        obj = getattr(mod, n, None)
        if isinstance(obj, dg.Definitions):
            return obj
        load_fn = getattr(obj, "load_fn", None)          # dagster.components.definitions.LazyDefinitions
        if load_fn is not None:
            return load_fn(dg.ComponentLoadContext.for_test()) if obj.has_context_arg else load_fn()
    raise LookupError(f"в модуле {mod.__name__} нет Definitions (ожидаю переменную {'/'.join(attrs)} или @definitions)")


def describe(defs) -> dict:
    graph = defs.resolve_asset_graph()
    assets = []
    blocking = {}                                          # (asset, check) -> blocking; check_specs есть и у assets_def, и у @asset_check
    for ac in defs.asset_checks or []:
        for cs in _safe(lambda: ac.check_specs, []):
            blocking[(cs.asset_key.to_user_string(), cs.name)] = bool(getattr(cs, "blocking", False))
    for key in sorted(graph.get_all_asset_keys(), key=str):
        n = graph.get(key)
        ad = n.assets_def
        for cs in _safe(lambda: ad.check_specs, []):
            blocking[(cs.asset_key.to_user_string(), cs.name)] = bool(getattr(cs, "blocking", False))
        cond = _safe(lambda: n.automation_condition)
        fresh = _safe(lambda: n.freshness_policy) or _safe(lambda: n.legacy_freshness_policy)
        assets.append({
            "key": key.to_user_string(),
            "group": n.group_name,
            "parents": sorted(p.to_user_string() for p in n.parent_keys),
            "kinds": sorted(n.kinds),
            "external": bool(n.is_external),
            "automation_condition": (_safe(cond.get_label) or type(cond).__name__) if cond is not None else None,
            "freshness": str(fresh) if fresh is not None else None,
            "retry": _safe(lambda: ad.op.retry_policy) is not None,
            "metadata_keys": sorted(n.metadata or {}),
        })
    schedules = []
    for s in defs.schedules or []:
        job = _safe(lambda: defs.resolve_job_def(s.job_name))
        keys = _safe(lambda: sorted(k.to_user_string() for k in job.asset_layer.executable_asset_keys), [])
        schedules.append({"name": s.name, "cron": s.cron_schedule, "timezone": s.execution_timezone,
                          "job": s.job_name, "asset_keys": keys})
    return {
        "ok": True,
        "dagster_version": _safe(lambda: importlib.metadata.version("dagster")),
        "assets": assets,
        "checks": [{"asset": k.asset_key.to_user_string(), "name": k.name,
                    "blocking": blocking.get((k.asset_key.to_user_string(), k.name), False)}
                   for k in sorted(graph.asset_check_keys, key=str)],
        "schedules": schedules,
        # run_failure_sensor — это RunStatusSensorDefinition; отличаем по статусу, на который он реагирует
        "sensors": [{"name": s.name, "type": type(s).__name__,
                     "run_status": _safe(lambda: s._run_status.value)} for s in defs.sensors or []],
        "jobs": [j.name for j in defs.jobs or []],
        "resources": sorted(defs.resources or {}),
    }


def events(home: str) -> dict:
    """Итоги запусков из инстанса в DAGSTER_HOME: статусы запусков, материализованные ассеты, результаты checks."""
    import os

    os.environ["DAGSTER_HOME"] = home
    from dagster import DagsterEventType, DagsterInstance, EventRecordsFilter

    inst = DagsterInstance.get()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mats = inst.get_event_records(EventRecordsFilter(event_type=DagsterEventType.ASSET_MATERIALIZATION), limit=5000)
        evals = inst.get_event_records(EventRecordsFilter(event_type=DagsterEventType.ASSET_CHECK_EVALUATION), limit=5000)
    latest: dict[tuple[str, str], bool] = {}
    for r in evals:                                        # новейшие первыми: оставляем последний результат каждого check
        e = r.event_log_entry.dagster_event.event_specific_data
        latest.setdefault((e.asset_key.to_user_string(), e.check_name), bool(e.passed))
    return {
        "ok": True,
        "runs": [{"id": r.run_id, "status": r.status.value} for r in inst.get_runs()],
        "materialized": sorted({r.asset_key.to_user_string() for r in mats if r.asset_key}),
        "checks": [{"asset": a, "name": n, "passed": p} for (a, n), p in sorted(latest.items())],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--module", help="модуль с Definitions (HW_DAGSTER_MODULE)")
    ap.add_argument("--attr", action="append", default=[], help="имя переменной/функции с Definitions (можно несколько)")
    ap.add_argument("--events", metavar="DAGSTER_HOME", help="вместо графа — итоги запусков из этого инстанса")
    a = ap.parse_args()
    if bool(a.module) == bool(a.events):
        ap.error("нужен ровно один из --module / --events")
    try:
        out = events(a.events) if a.events else describe(resolve_defs(importlib.import_module(a.module), a.attr))
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        out = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}", "trace_tail": tb[-6:]}
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
