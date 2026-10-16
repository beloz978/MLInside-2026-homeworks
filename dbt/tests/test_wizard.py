import os
from pathlib import Path

import pytest

import wizard


@pytest.fixture
def project(tmp_path):
    (tmp_path / "dbt_project.yml").write_text("name: x\n", encoding="utf-8")
    (tmp_path / "profiles.yml").write_text("x: {}\n", encoding="utf-8")
    return tmp_path


def test_step_project_writes_absolute_paths(project):
    out = wizard.step_project(True, os.path.relpath(project, wizard.ROOT))   # относительный ввод → абсолютный путь
    assert Path(out["HW_DBT_PROJECT_DIR"]) == project
    assert Path(out["HW_DBT_PROFILES_DIR"]) == project


def test_step_project_keeps_symlink(project, tmp_path_factory):
    link = tmp_path_factory.mktemp("links") / "dbt"
    link.symlink_to(project)
    out = wizard.step_project(True, str(link))
    assert out["HW_DBT_PROJECT_DIR"] == str(link)


def test_non_interactive_requires_project(monkeypatch, capsys):
    monkeypatch.delenv("HW_DBT_PROJECT_DIR", raising=False)
    monkeypatch.setattr(wizard, "load_env", lambda: None)
    monkeypatch.setattr("sys.argv", ["wizard.py", "-ni"])
    assert wizard.main() == 2
    assert "--project" in capsys.readouterr().out
