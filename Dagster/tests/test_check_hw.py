import copy
import json
import os
import subprocess
import sys

import pytest

import check_hw
from criteria import points

GH_OK = {"repo": "o/r", "pr": {"number": 1, "url": "https://x/1", "title": "Dagster HW", "state": "open", "merged": False,
                               "body_len": 200, "has_image": True, "has_versions": True, "has_ci_link": False, "sha": "abc"}}
MARTS_OK = {m: {"present": True, "columns_ok": True, "assert_ok": True, "problems": []}
            for m in ("mart_delivery_by_state", "mart_customer_profile")}
RAW_OK = ([(f"t{i}", True, "ok") for i in range(8)], 8, 8)
EVENTS_OK = {"ok": True, "runs": [{"id": "r", "status": "SUCCESS"}], "materialized": [],
             "checks": [{"asset": "stg_orders", "name": "c", "passed": True}]}


@pytest.fixture
def readme(tmp_path):
    f = tmp_path / "README.md"
    f.write_text("## Установка\n`uv sync`\n## Запуск\n`dagster dev`\n", encoding="utf-8")
    return f


def ctx7(info, rd, **kw):
    base = dict(info=info, events=EVENTS_OK, run_rc=0, raw=RAW_OK, marts=MARTS_OK, readme=rd, gh=GH_OK)
    return check_hw.Ctx(rd.parent, **{**base, **kw})  # kw перекрывает base, в т.ч. readme=None


def passed(criteria):
    return [c.n for c in criteria if c.passed]


def test_tier7_scores_six_and_7_to_10_are_not_checked(tier7_info, readme):
    cs = check_hw.evaluate(ctx7(tier7_info, readme))
    assert passed(cs) == [1, 2, 3, 4, 5, 6]
    assert points(cs) == 6 and check_hw.level_name(6) == "6–7 баллов"
    assert all(c.subs[0].status == "info" for c in cs[6:])


def test_empty_template_scores_zero(empty_info, tmp_path):
    cs = check_hw.evaluate(check_hw.Ctx(tmp_path, info=empty_info))
    assert points(cs) == 0 and check_hw.level_name(0) == "ниже 6 баллов"


def test_no_gh_caps_tier7_at_five(tier7_info, readme):
    assert passed(check_hw.evaluate(ctx7(tier7_info, readme, gh=None))) == [1, 2, 3, 4, 5]


def test_external_asset_is_a_lineage_gap(tier7_info, readme):
    info = copy.deepcopy(tier7_info)
    info["assets"].append({"key": "raw/orders", "group": "raw", "parents": [], "kinds": [], "external": True,
                           "automation_condition": None, "freshness": None, "retry": False, "metadata_keys": []})
    c3 = check_hw.evaluate(ctx7(info, readme))[2]
    assert not c3.passed and any("lineage без разрывов" in s.text and s.status == "fail" for s in c3.subs)


def test_failed_check_and_no_run_fail_criterion_4(tier7_info, readme):
    bad = {**EVENTS_OK, "checks": [{"asset": "stg_orders", "name": "c", "passed": False}]}
    assert 4 not in passed(check_hw.evaluate(ctx7(tier7_info, readme, events=bad)))
    assert 4 not in passed(check_hw.evaluate(ctx7(tier7_info, readme, events={})))


def test_marts_must_match_control_figures(tier7_info, readme):
    one = {k: v for k, v in list(MARTS_OK.items())[:1]}
    assert 4 not in passed(check_hw.evaluate(ctx7(tier7_info, readme, marts=one)))


@pytest.mark.parametrize("cron, ok", [("0 6 * * *", True), ("@daily", True), ("*/5 * * * *", False), ("0 6 * * 1", False)])
def test_daily_cron(tier7_info, readme, cron, ok):
    info = copy.deepcopy(tier7_info)
    info["schedules"][0]["cron"] = cron
    assert (5 in passed(check_hw.evaluate(ctx7(info, readme)))) is ok


def test_schedule_must_cover_marts(tier7_info, readme):
    info = copy.deepcopy(tier7_info)
    info["schedules"][0]["asset_keys"] = ["olist_orders_dataset"]
    assert 5 not in passed(check_hw.evaluate(ctx7(info, readme)))


def test_pr_without_screenshot_or_versions_fails(tier7_info, readme):
    for key in ("has_image", "has_versions"):
        gh = {**GH_OK, "pr": {**GH_OK["pr"], key: False}}
        assert 6 not in passed(check_hw.evaluate(ctx7(tier7_info, readme, gh=gh)))


def test_readme_needs_install_and_run(tier7_info, tmp_path):
    f = tmp_path / "README.md"
    f.write_text("# проект\nпросто текст\n", encoding="utf-8")
    assert 6 not in passed(check_hw.evaluate(ctx7(tier7_info, f)))
    assert 6 not in passed(check_hw.evaluate(ctx7(tier7_info, f, readme=None)))


def test_every_failed_sub_of_an_empty_project_has_a_hint(empty_info, tmp_path):
    import yaml

    hints = yaml.safe_load((check_hw.ROOT / "data" / check_hw.S["hints_file"]).read_text(encoding="utf-8"))
    cs = check_hw.evaluate(check_hw.Ctx(tmp_path, info=empty_info, gh={"error": "нет токена"}))
    missing = [s.text for c in cs[:6] for s in c.subs if s.status == "fail" and not check_hw.hint_for(s.text, hints)]
    assert not missing, missing


def test_main_on_empty_fixture_end_to_end(tmp_path):
    """Настоящий запуск `check_hw.py --no-run --no-gh --json` на фикстуре empty: 0 баллов, 10 критериев."""
    proj = check_hw.ROOT / "tests" / "fixtures" / "empty"
    env = {**os.environ, "HW_DAGSTER_PROJECT_DIR": str(proj), "HW_DAGSTER_MODULE": "empty_proj",
           "OLIST_DUCKDB_PATH": str(tmp_path / "none.duckdb"), "HW_DAGSTER_PYTHON": sys.executable}
    r = subprocess.run([sys.executable, str(check_hw.ROOT / "scripts" / "check_hw.py"), "--no-run", "--no-gh", "--json", "--min", "0"],
                       env=env, capture_output=True, text=True)
    out = json.loads(r.stdout)
    assert r.returncode == 0 and out["points"] == 0 and out["max"] == 10 and len(out["criteria"]) == 10
