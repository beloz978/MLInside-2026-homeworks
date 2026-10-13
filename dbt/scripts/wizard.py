#!/usr/bin/env python3
"""Интерактивный мастер настройки: GitHub, путь к проекту, СУБД и креды → .env и .env.local.

Шаги:
  1) 🐙 GitHub: проверяет `gh auth status`; предлагает войти через браузер (`gh auth login`)
     или вставить персональный токен (ввод скрыт), определяет репозиторий и PR;
  2) 📁 путь к dbt-проекту и каталогу profiles.yml (ищет dbt_project.yml рядом);
  3) 🗄️ второй таргет: нет / Postgres / ClickHouse — параметры подключения и пароль;
  4) 📝 пишет .env (несекретное) и .env.local (токен GitHub, пароли), старый файл сохраняет как *.bak;
  5) 🔌 по желанию проверяет подключение к СУБД и GitHub.

Секреты никогда не печатаются и не попадают в .env (только в .env.local, он в .gitignore).
Без вопросов (CI/тест): python scripts/wizard.py -ni|--non-interactive --project PATH [--db postgres ...]
  (--project обязателен, если HW_DBT_PROJECT_DIR не задан в config/.env или окружении)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import ENV_DIR, ROOT, load_env, parse_env  # noqa: E402
from settings import section  # noqa: E402
from utils import ask, choose, resolve_path, update_env_file, yesno  # noqa: E402

S = section("wizard")
EXISTING = parse_env(ENV_DIR / ".env")      # уже записанные значения: умолчания из settings.yml их не затирают


# ------------------------------------------------------------------ шаги
def step_github(ni: bool, project: Path | None) -> dict[str, str]:
    print("\n🐙 Шаг 1/3 — GitHub (нужен, чтобы проверить, что PR создан и заполнен)")
    secrets: dict[str, str] = {}
    gh = shutil.which("gh")
    logged = False
    if gh:
        r = subprocess.run([gh, "auth", "status"], capture_output=True, text=True)
        logged = r.returncode == 0
        print("   ✅ GitHub CLI (gh) найден, вход выполнен" if logged else "   ⚠️  GitHub CLI (gh) найден, но вход не выполнен")
    else:
        print("   🆗 GitHub CLI (gh) не установлен — можно вставить токен вручную")
    if not logged and not ni:
        how = choose("Как авторизоваться?", [
            ("web", "через браузер (gh auth login --web)" + ("" if gh else " — gh не установлен")),
            ("token", "вставить персональный токен (Settings → Developer settings → fine-grained, права: Pull requests: Read, Actions: Read, Metadata: Read)"),
            ("skip", "пропустить (критерий «PR» и CI не будут засчитаны)")], default=0 if gh else 1)
        if how == "web" and gh:
            subprocess.call([gh, "auth", "login", "--web", "--git-protocol", "https"])
        elif how == "token":
            tok = ask("Токен GitHub", secret=True)
            if tok:
                secrets["GH_TOKEN"] = tok
    import gh_api  # noqa: E402

    if secrets.get("GH_TOKEN"):
        os.environ["GH_TOKEN"] = secrets["GH_TOKEN"]
    token = gh_api.get_token()
    if token:
        try:
            print(f"   ✅ авторизован как {gh_api.api('/user', token)['login']}")
        except Exception as e:  # noqa: BLE001
            print(f"   ❌ токен не работает: {type(e).__name__}")
    out: dict[str, str] = {}
    repo = gh_api.detect_repo(project) if project else None
    repo = ask("Репозиторий с вашим PR (owner/name)", repo or os.environ.get("HW_GH_REPO", ""), ni=ni)
    if repo:
        out["HW_GH_REPO"] = repo
    pr = ask("Номер PR (пусто = взять PR текущей ветки / последний ваш)", os.environ.get("HW_GH_PR", ""), ni=ni)
    out["HW_GH_PR"] = pr
    if repo and not ni:
        verify_repo_pr(gh_api, repo, pr, token, project)
    return {**out, **{"__secret__" + k: v for k, v in secrets.items()}}


def verify_repo_pr(gh_api, repo: str, pr: str, token: str | None, project: Path | None) -> None:
    """Печатает, виден ли репозиторий и найден ли PR; ничего не прерывает (GitHub-шаг можно пропустить)."""
    url = S["repo_url"].format(repo=repo)
    print(f"   🔗 {url}")
    try:
        gh_api.api(f"/repos/{repo}", token)
    except urllib.error.HTTPError as e:
        print(f"   ❌ нет доступа к {url} (HTTP {e.code}): проверьте имя owner/name и права токена")
        return
    except Exception as e:  # noqa: BLE001
        print(f"   ❌ GitHub недоступен: {type(e).__name__}")
        return
    old = os.environ.get("HW_GH_PR")
    os.environ["HW_GH_PR"] = pr                      # find_pr читает номер из окружения
    try:
        found = gh_api.find_pr(repo, token, project or Path.cwd())
    except ValueError:
        print(f"   ❌ номер PR должен быть числом, получено «{pr}»")
        return
    except urllib.error.HTTPError as e:
        print(f"   ❌ PR #{pr} не найден в {url} (HTTP {e.code})")
        return
    finally:
        os.environ.pop("HW_GH_PR", None) if old is None else os.environ.__setitem__("HW_GH_PR", old)
    if found:
        print(f"   ✅ PR #{found['number']} «{found['title']}»: {found['html_url']}")
    else:
        print(f"   ⚠️  открытых и закрытых PR в {url} не найдено — создайте PR из ветки с ДЗ")


def find_projects(start: Path) -> list[Path]:
    found: list[Path] = []
    for base in (Path.cwd(), start, start.parent):
        if base.exists():
            for p in list(base.glob("dbt_project.yml")) + list(base.glob("*/dbt_project.yml")) + list(base.glob("*/*/dbt_project.yml")):
                if "dbt_packages" not in p.parts and p.parent not in found:
                    found.append(p.parent)
    return found


def tilde(p: Path) -> str:
    """Путь с ~ вместо домашнего каталога — для вывода."""
    try:
        return "~/" + p.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(p)


def profile_names(profiles_dir: Path) -> list[str] | None:
    f = profiles_dir / "profiles.yml"
    if not f.exists():
        return None
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return [k for k in data if k != "config"]       # config — служебная секция dbt, не профиль


def step_project(ni: bool, project_arg: str | None) -> dict[str, str]:
    print("\n📁 Шаг 2/3 — путь к вашему dbt-проекту")
    cur = project_arg or os.environ.get("HW_DBT_PROJECT_DIR", "")
    cands = find_projects(ROOT.parent)
    if cands and not cur:
        print("   🔎 найдено рядом:")
        for c in cands[:5]:
            print(f"      • {tilde(c)}")
        cur = str(cands[0].resolve())
    while True:
        v = ask("Каталог с dbt_project.yml", cur, ni=ni)
        p = resolve_path(v, ROOT)
        if (p / "dbt_project.yml").exists():
            print(f"   ✅ найден {tilde(p / 'dbt_project.yml')}")
            break
        print(f"   ❌ нет dbt_project.yml в {tilde(p)} (введено «{v}»; относительные пути считаются от {tilde(ROOT)})")
        if ni:
            sys.exit(2)
    prof = p if (p / "profiles.yml").exists() else None
    pv = ask("Каталог с profiles.yml", str(prof or p), ni=ni)
    pp = resolve_path(pv, ROOT)
    print(f"   ✅ profiles.yml на месте: {tilde(pp)}" if (pp / "profiles.yml").exists() else f"   ⚠️  profiles.yml в {tilde(pp)} не найден")
    name = ask("Имя профиля в profiles.yml", os.environ.get("HW_DBT_PROFILE") or EXISTING.get("HW_DBT_PROFILE") or S["profile"], ni=ni)
    names = profile_names(pp)
    if names is None:
        print(f"   ⚠️  профиль «{name}» не проверен: нет profiles.yml")
    elif name in names:
        print(f"   ✅ профиль «{name}» найден в profiles.yml")
    else:
        print(f"   ❌ профиля «{name}» нет в profiles.yml (есть: {', '.join(names) or 'пусто'})")
    # абсолютные пути без раскрытия симлинков: остаётся тот путь, что указал пользователь
    return {"HW_DBT_PROJECT_DIR": os.path.abspath(p), "HW_DBT_PROFILES_DIR": os.path.abspath(pp), "HW_DBT_PROFILE": name}


def step_db(ni: bool, kind_arg: str | None, args: argparse.Namespace) -> tuple[dict[str, str], dict[str, str]]:
    print("\n🗄️  Шаг 3/3 — второй таргет для 10 баллов (DuckDB есть всегда)")
    kind = kind_arg or choose("Что используете как второй таргет?", [
        ("none", "ничего (только DuckDB)"), ("postgres", "Postgres"), ("clickhouse", "ClickHouse")], ni=ni)
    plain: dict[str, str] = {
        "HW_DBT_TARGETS": S["targets"],
        "OLIST_DUCKDB_PATH": EXISTING.get("OLIST_DUCKDB_PATH") or S["duckdb_path"],
        "CONTROL_FIGURES_JSON": EXISTING.get("CONTROL_FIGURES_JSON") or S["control_figures_json"]}
    secret: dict[str, str] = {}
    if kind == "none":
        plain["HW_SECOND_TARGET"] = ""
        return plain, secret
    d = S["db_defaults"][kind]
    pre = "PG" if kind == "postgres" else "CLICKHOUSE_"
    host = ask("Хост", args.db_host or d["host"], ni=ni)
    port = ask("Порт" + (" (8123 HTTP, 9000 native)" if kind == "clickhouse" else ""), args.db_port or d["port"], ni=ni)
    user = ask("Пользователь", args.db_user or d["user"], ni=ni)
    dbn = ask("База данных", args.db_name or d["db"], ni=ni)
    pw = args.db_password if args.db_password is not None else ask("Пароль (ввод скрыт)", "", secret=True, ni=ni)
    names = ("HOST", "PORT", "USER", "DATABASE") if kind == "clickhouse" else ("HOST", "PORT", "USER", "DATABASE")
    for n, v in zip(names, (host, port, user, dbn)):
        plain[f"{pre}{n}"] = v
    secret[f"{pre}PASSWORD"] = pw
    plain["HW_SECOND_TARGET"] = ask("Имя output в profiles.yml для этого таргета", kind, ni=ni)
    plain["HW_DBT_TARGETS"] = f"duckdb,{plain['HW_SECOND_TARGET']}"
    print(f"   🆗 нужен драйвер: pip install {S['db_drivers'][kind]}"
          "   (раскомментируйте в config/requirements.txt и выполните `make setup`)")
    return plain, secret


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-ni", "--non-interactive", action="store_true", help="без вопросов: значения из аргументов/окружения/умолчаний")
    ap.add_argument("--project", help="каталог dbt-проекта (обязателен с -ni, если нет HW_DBT_PROJECT_DIR в config/.env)")
    ap.add_argument("--db", choices=["none", "postgres", "clickhouse"])
    ap.add_argument("--db-host"); ap.add_argument("--db-port"); ap.add_argument("--db-user")  # noqa: E702
    ap.add_argument("--db-name"); ap.add_argument("--db-password")  # noqa: E702
    ap.add_argument("--skip-github", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="показать, что будет записано, не меняя файлы")
    a = ap.parse_args()
    ni = a.non_interactive
    if not ni and not sys.stdin.isatty():
        print("❌ мастер интерактивный: запустите его в терминале (или добавьте -ni / --non-interactive)")
        return 2
    load_env()                                   # окружение > .env.local > .env — как в остальных скриптах
    if ni and not (a.project or os.environ.get("HW_DBT_PROJECT_DIR")):
        print("❌ с -ni нужен путь к dbt-проекту: --project PATH или HW_DBT_PROJECT_DIR в config/.env")
        return 2

    print("🧙 Мастер настройки самопроверки MLInside\n   Файлы config/.env (несекретное) и config/.env.local (секреты). Ctrl+C — выход без записи.")
    plain: dict[str, str] = {}
    secrets: dict[str, str] = {}
    try:
        plain.update(step_project(ni, a.project))
        proj = (ROOT / plain["HW_DBT_PROJECT_DIR"]).resolve()
        if not a.skip_github:
            g = step_github(ni, proj)
            for k, v in g.items():
                (secrets if k.startswith("__secret__") else plain)[k.replace("__secret__", "")] = v
        p2, s2 = step_db(ni, a.db, a)
        plain.update(p2)
        secrets.update(s2)
    except KeyboardInterrupt:
        print("\n⏹️  Прервано, ничего не записано.")
        return 130

    print("\n📝 Будет записано:")
    for k, v in plain.items():
        print(f"   .env        {k}={v}")
    for k in secrets:
        print(f"   .env.local  {k}=******")
    if a.dry_run:
        print("🆗 --dry-run: файлы не изменены")
        return 0
    if not ni and not yesno("Записать?", True):
        print("⏹️  Отменено.")
        return 1
    update_env_file(ENV_DIR / ".env", plain, "# Создано мастером scripts/wizard.py. Секреты — в .env.local.")
    if secrets:
        update_env_file(ENV_DIR / ".env.local", secrets, "# Секреты. Не коммитить (.gitignore).")
    print(f"✅ Готово: записан {tilde(ENV_DIR / '.env')}" + (f" и {tilde(ENV_DIR / '.env.local')}" if secrets else "")
          + " (прежние версии — *.bak рядом)")

    if not ni and plain.get("HW_SECOND_TARGET") and yesno("Проверить подключение к СУБД сейчас?", True):
        env = {**os.environ, **{k: v for k, v in {**plain, **secrets}.items()}}
        subprocess.call([sys.executable, str(ROOT / "scripts" / "check_db_from_profile.py"),
                         "--profiles-dir", str((ROOT / plain["HW_DBT_PROFILES_DIR"]).resolve()),
                         "--profile", plain["HW_DBT_PROFILE"], "--targets", plain["HW_SECOND_TARGET"]], env=env)
    print("➡️  Дальше: `make seeds`, затем `make ready` и `make check`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
