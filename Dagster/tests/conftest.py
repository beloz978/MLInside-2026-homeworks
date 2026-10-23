import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

collect_ignore_glob = ["fixtures/*"]                  # тесты внутри фикстур — данные для чекера, а не наши тесты
DAGSTER = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(DAGSTER.parent / "dbt" / "scripts"))
sys.path.insert(0, str(DAGSTER / "scripts"))          # первым: в обоих каталогах есть check_hw.py, нужен Dagster-овский


def inspect_fixture(name: str, module: str) -> dict:
    """Описание фикстурного проекта настоящим inspect_defs.py (интерпретатор — текущий, dagster в нём стоит)."""
    proj = FIXTURES / name
    r = subprocess.run([sys.executable, str(DAGSTER / "scripts" / "inspect_defs.py"), "--module", module, "--attr", "defs"],
                       cwd=proj, env={**os.environ, "PYTHONPATH": str(proj)}, capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    assert lines, f"inspect_defs не вывел JSON (rc={r.returncode}): {r.stderr[-600:]}"
    return json.loads(lines[-1])


@pytest.fixture(scope="session")
def tier7_info() -> dict:
    return inspect_fixture("tier7", "t7_proj")


@pytest.fixture(scope="session")
def tier9_info() -> dict:
    return inspect_fixture("tier9", "t9_proj")


@pytest.fixture(scope="session")
def empty_info() -> dict:
    return inspect_fixture("empty", "empty_proj")
