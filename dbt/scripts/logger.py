"""Вывод статусов для скриптов самопроверки: строки [OK  ]/[FAIL]/[skip] и эмодзи отчёта."""
from __future__ import annotations

import os
import sys

EMO = {"ok": "✅", "fail": "❌", "warn": "⚠️ ", "info": "🆗"}
MARK = {True: "OK  ", False: "FAIL", None: "skip"}


class Checks:
    """Печатает строки проверок и считает провалы: ok=False — провал, None — пропуск."""

    def __init__(self, hints: dict[str, str] | None = None) -> None:
        self.bad = 0
        self.hints = hints or {}
        self.red, self.reset = ("\033[1;31m", "\033[0m") if sys.stdout.isatty() and "NO_COLOR" not in os.environ else ("", "")

    def line(self, ok: bool | None, label: str, detail: str = "", hint: str = "") -> None:
        """hint — ключ в hints; подсказка 💡 печатается только под FAIL."""
        self.bad += ok is False
        text = f"[{MARK[ok]}] {label:<26} {detail}"
        print(f"{self.red}{text}{self.reset}" if ok is False else text)
        if ok is False and hint in self.hints:
            print(f"   💡 {self.hints[hint]}")


def target_line(r: dict) -> str:
    """Строка результата проверки target: {target, type, ok, ms, message}."""
    return f"[{'OK ' if r['ok'] else 'FAIL'}] {r['target']:<12} {r['type'] or '?':<11} {r['ms']:>5} ms  {r['message']}"
