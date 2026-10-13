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
Без вопросов (CI/тест): python scripts/wizard.py --non-interactive --project PATH [--db postgres ...]
"""
from __future__ import annotations

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from envload import ENV_DIR, ROOT, parse_env  # noqa: E402
from settings import section  # noqa: E402

S = section("wizard")


# ------------------------------------------------------------------ .env helpers
def update_env_file(path: Path, values: dict[str, str], header: str = "") -> None:
    """Меняет/добавляет ключи, сохраняя остальные строки и комментарии. Старый файл → .bak."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else ([header] if header else [])
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + ".bak"))
    seen: set[str] = set()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s and not s.startswith("#") and "=" in s:
            k = s.split("=", 1)[0].strip()
            if k in values:
                lines[i] = f"{k}={values[k]}"
                seen.add(k)
    for k, v in values.items():
        if k not in seen:
            lines.append(f"{k}={v}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    if path.name == ".env.local" and os.name == "posix":
        path.chmod(0o600)


def ask(q: str, default: str = "", secret: bool = False, ni: bool = False) -> str:
    if ni:
        return default
    suffix = f" [{'скрыто' if secret and default else default}]" if default else ""
    try:
        v = (getpass.getpass if secret else input)(f"❓ {q}{suffix}: ").strip()
    except EOFError:
        return default
    return v or default


def yesno(q: str, default: bool = True, ni: bool = False) -> bool:
    if ni:
        return default
    v = ask(f"{q} ({'Д/н' if default else 'д/Н'})").lower()
    return default if not v else v[0] in "yд1"


def choose(q: str, options: list[tuple[str, str]], default: int = 0, ni: bool = False) -> str:
    if ni:
        return options[default][0]
    print(f"❓ {q}")
    for i, (_, label) in enumerate(options, 1):
        print(f"   {i}) {label}")
    v = ask("Номер", str(default + 1))
    try:
        return options[int(v) - 1][0]
    except (ValueError, IndexError):
        return options[default][0]


# ------------------------------------------------------------------ шаги
def step_github(ni: bool, project: Path | None) -> dict[str, str]:
    print("\n🐙 Шаг 1/3 — GitHub (нужен, чтобы проверить, что PR создан и заполнен)")
    secrets: dict[str, str] = {}
    gh = shutil.which("gh")
    logged = False
    if gh:
        r = subprocess.run([gh, "auth", "status"], capture_output=True, text=True)
        logged = r.returncode == 0
        print("   ✅ gh найден, вход выполнен" if logged else "   ⚠️  gh найден, но вход не выполнен")
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
    return {**out, **{"__secret__" + k: v for k, v in secrets.items()}}


def find_projects(start: Path) -> list[Path]:
    found: list[Path] = []
    for base in (Path.cwd(), start, start.parent):
        if base.exists():
            for p in list(base.glob("dbt_project.yml")) + list(base.glob("*/dbt_project.yml")) + list(base.glob("*/*/dbt_project.yml")):
                if "dbt_packages" not in p.parts and p.parent not in found:
                    found.append(p.parent)
    return found


def rel(p: Path) -> str:
    try:
        return os.path.relpath(p, ROOT)
    except ValueError:                      # Windows: другой диск
        return str(p)


def step_project(ni: bool, project_arg: str | None) -> dict[str, str]:
    print("\n📁 Шаг 2/3 — путь к вашему dbt-проекту")
    cur = project_arg or os.environ.get("HW_DBT_PROJECT_DIR", "")
    cands = find_projects(ROOT.parent)
    if cands and not cur:
        print("   🔎 найдено рядом:")
        for c in cands[:5]:
            print(f"      • {rel(c)}")
        cur = rel(cands[0])
    while True:
        v = ask("Каталог с dbt_project.yml", cur, ni=ni)
        p = Path(v).expanduser()
        p = p if p.is_absolute() else (ROOT / p)
        if (p / "dbt_project.yml").exists():
            print(f"   ✅ найден {p / 'dbt_project.yml'}")
            break
        print(f"   ❌ нет dbt_project.yml в {p}")
        if ni:
            sys.exit(2)
    prof = p if (p / "profiles.yml").exists() else None
    pv = ask("Каталог с profiles.yml", rel(prof or p), ni=ni)
    pp = Path(pv).expanduser()
    pp = pp if pp.is_absolute() else (ROOT / pp)
    print("   ✅ profiles.yml на месте" if (pp / "profiles.yml").exists() else "   ⚠️  profiles.yml там не найден")
    name = ask("Имя профиля в profiles.yml", os.environ.get("HW_DBT_PROFILE", "olist"), ni=ni)
    return {"HW_DBT_PROJECT_DIR": rel(p), "HW_DBT_PROFILES_DIR": rel(pp), "HW_DBT_PROFILE": name}


def step_db(ni: bool, kind_arg: str | None, args: argparse.Namespace) -> tuple[dict[str, str], dict[str, str]]:
    print("\n🗄️  Шаг 3/3 — второй таргет для 10 баллов (DuckDB есть всегда)")
    kind = kind_arg or choose("Что используете как второй таргет?", [
        ("none", "ничего (только DuckDB)"), ("postgres", "Postgres"), ("clickhouse", "ClickHouse")], ni=ni)
    plain: dict[str, str] = {"HW_DBT_TARGETS": "duckdb"}
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
    ap.add_argument("--non-interactive", action="store_true", help="без вопросов: значения из аргументов/окружения/умолчаний")
    ap.add_argument("--project", help="каталог dbt-проекта")
    ap.add_argument("--db", choices=["none", "postgres", "clickhouse"])
    ap.add_argument("--db-host"); ap.add_argument("--db-port"); ap.add_argument("--db-user")  # noqa: E702
    ap.add_argument("--db-name"); ap.add_argument("--db-password")  # noqa: E702
    ap.add_argument("--skip-github", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="показать, что будет записано, не меняя файлы")
    a = ap.parse_args()
    ni = a.non_interactive
    if not ni and not sys.stdin.isatty():
        print("❌ мастер интерактивный: запустите его в терминале (или добавьте --non-interactive)")
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
    print("✅ Готово: config/.env" + (" и config/.env.local" if secrets else "") + " обновлены (прежние версии — *.bak)")

    if not ni and plain.get("HW_SECOND_TARGET") and yesno("Проверить подключение к СУБД сейчас?", True):
        env = {**os.environ, **{k: v for k, v in {**plain, **secrets}.items()}}
        subprocess.call([sys.executable, str(ROOT / "scripts" / "check_db_from_profile.py"),
                         "--profiles-dir", str((ROOT / plain["HW_DBT_PROFILES_DIR"]).resolve()),
                         "--profile", plain["HW_DBT_PROFILE"], "--targets", plain["HW_SECOND_TARGET"]], env=env)
    print("➡️  Дальше: `just doctor`, затем `just check-hw`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
