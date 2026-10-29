import pytest

import settings


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Проект-двойник: <проект>/scripts/settings.yml; FILE возвращается после теста."""
    monkeypatch.setattr(settings, "FILE", settings.FILE)
    f = tmp_path / "proj" / "scripts" / "settings.yml"
    f.parent.mkdir(parents=True)
    f.write_text("doctor:\n  python_min: [3, 10]\n", encoding="utf-8")
    return f


def test_default_is_own_file():
    assert settings.FILE.name == "settings.yml" and settings.FILE.parent.name == "scripts"
    assert settings.root() == settings.FILE.parent.parent


def test_use_switches_section_and_root(project):
    settings.use(project)
    assert settings.section("doctor")["python_min"] == [3, 10]
    assert settings.root() == project.parent.parent


@pytest.mark.parametrize("form", ["split", "equals"])
def test_use_from_argv(project, form):
    argv = ["x.py", "--no-gh", "--settings", str(project)] if form == "split" else ["x.py", f"--settings={project}"]
    settings.use_from_argv(argv)
    assert settings.FILE == project.resolve()


def test_use_from_argv_without_flag_keeps_file(project):
    before = settings.FILE
    settings.use_from_argv(["x.py", "--json"])
    assert settings.FILE == before


def test_use_missing_file_names_path(tmp_path):
    with pytest.raises(ValueError, match="nope.yml"):
        settings.use(tmp_path / "nope.yml")


def test_missing_key_names_key_and_file(project):
    settings.use(project)
    with pytest.raises(ValueError, match=r"doctor\.tools.*settings\.yml"):
        settings.section("doctor")["tools"]
