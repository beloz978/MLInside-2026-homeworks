"""Вывод статусов для скриптов самопроверки: строки [OK  ]/[FAIL]/[skip] и эмодзи отчёта."""
from __future__ import annotations

EMO = {"ok": "✅", "fail": "❌", "warn": "⚠️ ", "info": "🆗"}
MARK = {True: "OK  ", False: "FAIL", None: "skip"}


class Checks:
    """Печатает строки проверок и считает провалы: ok=False — провал, None — пропуск."""

    def __init__(self) -> None:
        self.bad = 0

    def line(self, ok: bool | None, label: str, detail: str = "") -> None:
        self.bad += ok is False
        print(f"[{MARK[ok]}] {label:<26} {detail}")


def target_line(r: dict) -> str:
    """Строка результата проверки target: {target, type, ok, ms, message}."""
    return f"[{'OK ' if r['ok'] else 'FAIL'}] {r['target']:<12} {r['type'] or '?':<11} {r['ms']:>5} ms  {r['message']}"
