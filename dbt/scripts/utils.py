"""Общие мелкие помощники скриптов: пути, JSON, сравнение чисел, запись .env, интерактивные вопросы."""
from __future__ import annotations

import getpass
import json
import os
import shutil
from pathlib import Path


def resolve_path(value: str, base: Path) -> Path:
    """~ раскрывается, относительный путь считается от base."""
    p = Path(value).expanduser()
    return p if p.is_absolute() else base / p


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def close(a, b, rel: float, abs_: float = 0.0) -> bool:
    """|a-b| <= max(abs_, rel*|b|); None на любой стороне — не равно."""
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= max(abs_, rel * abs(float(b)))


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
    ##v = ask(f"{q} ({'Д/н' if default else 'д/Н'})").lower()
    v = ask(f"{q} ({'Y/n' if default else 'n/Y'})").lower()
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
