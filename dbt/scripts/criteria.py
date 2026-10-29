"""Общая модель критериев автопроверки ДЗ и вывод отчёта (dbt/ и Dagster/).

Критерий = набор подпроверок; балл даёт, только если ни одна не провалена и хоть одна пройдена.
Статусы подпроверок: ok | fail | warn | info (warn/info на балл не влияют)."""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from logger import EMO


@dataclass
class Sub:
    status: str  # ok | fail | warn | info
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


def points(criteria: list[Criterion]) -> int:
    return sum(c.passed for c in criteria)


def report_json(criteria: list[Criterion], *, max_points: int, level: str, project: Path) -> str:
    return json.dumps({"points": points(criteria), "max": max_points, "level": level, "project": str(project),
                       "criteria": [{"n": c.n, "title": c.title, "passed": c.passed, "subs": [asdict(s) for s in c.subs]}
                                    for c in criteria]}, ensure_ascii=False, indent=2)


def print_report(criteria: list[Criterion], *, title: str, project: Path, level: str, max_points: int,
                 hint_for: Callable[[str], dict | None], detail_ok_prefixes: tuple[str, ...] = ()) -> None:
    """Текстовый отчёт. detail у пройденных подпроверок печатаем, только если текст начинается с одного из префиксов."""
    pts = points(criteria)
    print(f"\n{'=' * 8} 📋 Отчёт: {title} {'=' * 8}\nПроект: {project}")
    for c in criteria:
        done = sum(s.status == "ok" for s in c.subs)
        total = sum(s.status in ("ok", "fail") for s in c.subs)
        print(f"\n{'🟢' if c.passed else '🔴'} Балл {c.n}/{max_points} — {c.title}  [{done}/{total}]")
        for s in c.subs:
            print(f"   {EMO[s.status]} {s.text}")
            if s.detail and (s.status != "ok" or s.text.startswith(detail_ok_prefixes)):
                for ln in s.detail.splitlines():
                    print(f"        {ln}")
            h = hint_for(s.text) if s.status in ("fail", "warn") else None
            if h:
                print(f"        💡 {h['hint']}")
                if h.get("url"):
                    print(f"        🔗 {h['url']}")
    bar = "".join("🟩" if c.passed else "⬜" for c in criteria)
    print(f"\n{'=' * 8} 🏁 Итог {'=' * 8}\n{bar}\n🎯 Проект прошёл на {pts} из {max_points} баллов — уровень «{level}»")
    miss = [f"{c.n}. {c.title}" for c in criteria if not c.passed]
    if miss:
        print("📌 Не хватает:")
        for m in miss:
            print(f"   • {m}")
