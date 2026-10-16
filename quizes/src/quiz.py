"""Interactive terminal quiz from quizes/<name>.yaml (made by md2yaml.py), with a JSONL event log per run.

Usage: uv run --with questionary --with pyyaml python quizes/src/quiz.py quizes/quiz-4-dagster
Only the main section is asked; reserve questions are skipped.
Keys: digits 1–9 pick (single) or toggle (multi) an option, Enter answers, the hint key shows the hint,
the pause key pauses the timer (settings: quizes/src/settings.yml + <quiz_dir>/settings.yml).
Log: <quiz_dir>/<log.dir>/<yymmdd-HHMMSS>-<quiz>-<user>.jsonl — who/where at start, then every move, (un)choice, hint, pause, answer.
"""
import getpass
import json
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import questionary
import yaml
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from questionary.prompts.common import InquirerControl

from settings import load_settings as load_merged, require

SHOW_HINT = object()  # returned by a prompt when the hint key is pressed
PAUSE = object()  # returned by a prompt when the pause key is pressed
IDENTITY_MODES = ("os_git", "ask", "env")


def load_settings(quiz_dir: Path) -> tuple[dict, dict]:
    """(quiz, log) sections of the merged settings; missing keys or bad values raise ValueError."""
    cfg = load_merged(quiz_dir)
    require(cfg, *(f"quiz.{k}" for k in ("hint_difficulties", "hint_position", "hint_key", "pause_key")),
            *(f"log.{k}" for k in ("dir", "identity", "identity_env")))
    quiz, log = cfg["quiz"], cfg["log"]
    if quiz["hint_position"] not in ("before", "after"):
        raise ValueError(f"{cfg['_files']}: quiz.hint_position must be before or after")
    if log["identity"] not in IDENTITY_MODES:
        raise ValueError(f"{cfg['_files']}: log.identity must be one of {', '.join(IDENTITY_MODES)}")
    return quiz, log


class Log:
    """Append-only JSONL: one event per line, flushed at once so an interrupted run keeps everything."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.f, self.t0 = path, open(path, "a", encoding="utf-8"), time.monotonic()
        self.q: str | None = None
        self.paused_ms = 0

    def emit(self, event: str, **fields) -> None:
        line = {"t": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                "ms": int((time.monotonic() - self.t0) * 1000), "q": self.q, "event": event, **fields}
        self.f.write(json.dumps(line, ensure_ascii=False) + "\n")
        self.f.flush()


@dataclass
class State:
    """What the user has on screen for one question; the keypress hook keeps it current."""
    pointer: int = 0
    selected: list[int] = field(default_factory=list)
    toggles: int = 0
    paused_ms: int = 0
    t0: float = field(default_factory=time.monotonic)

    def ms(self) -> int:
        return int((time.monotonic() - self.t0) * 1000) - self.paused_ms


def git(*args: str) -> str:
    """Output of a git command, or "" when git or the value is absent (it is data for the log, not config)."""
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def identity(log_cfg: dict, **io) -> dict:
    """Who takes the quiz; log.identity picks how the user name is obtained."""
    who = {"identity_mode": log_cfg["identity"], "os_user": getpass.getuser(), "host": socket.gethostname(),
           "git_name": git("config", "user.name"), "git_email": git("config", "user.email")}
    if log_cfg["identity"] == "ask":
        who["user"] = questionary.text("Имя / ник:", validate=lambda s: bool(s.strip()) or "Введите имя",
                                       **io).unsafe_ask().strip()
    elif log_cfg["identity"] == "env":
        var = log_cfg["identity_env"]
        if var not in os.environ:
            raise ValueError(f"log.identity: env needs ${var} (set it in your .env / shell)")
        who["user"] = os.environ[var]
    else:
        who["user"] = who["os_user"]
    return who


def score(q: dict, picked: list[int]) -> tuple[int, int]:
    """(got, max). Multi: +1 per correct pick, −1 per wrong pick, not below 0. Single: 1/0."""
    correct = {i for i, o in enumerate(q["options"]) if o["correct"]}
    if q["multi"]:
        return max(0, len(correct & set(picked)) - len(set(picked) - correct)), len(correct)
    return int(picked == [next(iter(correct))]), 1


def add_hotkeys(question: questionary.Question, multi: bool, exits: dict, state: State, log: Log) -> questionary.Question:
    """Digits 1–9 toggle (multi) or point at (single) an option; keys in `exits` end the prompt with their sentinel.
    Restores `state` (selection survives hint/pause redraws) and logs every pointer move and (un)choice."""
    app = question.application
    # ponytail: reaches into questionary 2.x internals (InquirerControl.pointed_at/selected_options); recheck on upgrade
    ic = next(c for c in app.layout.find_all_controls() if isinstance(c, InquirerControl))
    ic.pointed_at = state.pointer
    if multi:
        ic.selected_options = list(state.selected)
    kb = KeyBindings()
    for i in range(min(9, ic.choice_count)):
        @kb.add(str(i + 1), eager=True)
        def _(event, i=i):
            ic.pointed_at = i
            if multi:
                value = ic.choices[i].value
                ic.selected_options.remove(value) if value in ic.selected_options else ic.selected_options.append(value)
    for key, sentinel in exits.items():
        @kb.add(key, eager=True)
        def _(event, sentinel=sentinel):
            event.app.erase_when_done = True  # the prompt is redrawn afterwards, don't leave this copy
            event.app.exit(result=sentinel)
    app.key_bindings = merge_key_bindings([app.key_bindings, kb])

    kp = app.key_processor

    def after_key(_):
        # ponytail: _previous_key_sequence is prompt_toolkit-private; it names the key that ran the last handler
        seq = kp._previous_key_sequence
        key = str(getattr(seq[-1].key, "value", seq[-1].key)) if seq else "?"
        if ic.pointed_at != state.pointer:
            log.emit("move", **{"from": state.pointer, "to": ic.pointed_at, "key": key})
            state.pointer = ic.pointed_at
        if multi:
            now = list(ic.selected_options)
            for o in sorted(set(now) - set(state.selected)):
                log.emit("choose", option=o, key=key)
            for o in sorted(set(state.selected) - set(now)):
                log.emit("unchoose", option=o, key=key)
            state.toggles += len(set(now) ^ set(state.selected))
            state.selected = now

    kp.after_key_press += after_key
    return question


def hints_of(q: dict, settings: dict) -> list[str]:
    """Hints in the order to show them (light → detailed); none for difficulties outside hint_difficulties."""
    return q.get("hints") or [] if q.get("difficulty") in settings["hint_difficulties"] else []


def prompt(q: dict, hints_shown: int, settings: dict, state: State, log: Log, **io) -> object:
    hints = hints_of(q, settings)
    bullets = "\n".join(f"  • 💡 {i}/{len(hints)} {h}" for i, h in enumerate(hints[:hints_shown], 1)) if len(hints) > 1 \
        else "\n".join(f"  • 💡 {h}" for h in hints[:hints_shown])
    message = q["text"]
    if bullets:
        if settings["hint_position"] == "before":
            print(bullets)
        else:
            message = f"{message}\n{bullets}"
    keys = "цифры — " + ("отметить, пробел тоже" if q["multi"] else "выбрать") + ", Enter — ответить"
    exits = {settings["pause_key"]: PAUSE}
    if hints_shown < len(hints):
        keys += f", {settings['hint_key']} — подсказка" + (f" {hints_shown + 1}/{len(hints)}" if len(hints) > 1 else "")
        exits[settings["hint_key"]] = SHOW_HINT
    keys += f", {settings['pause_key']} — пауза"
    choices = [questionary.Choice(f"{i + 1}) {o['text']}", value=i) for i, o in enumerate(q["options"])]
    factory = questionary.checkbox if q["multi"] else questionary.select
    question = factory(message, choices=choices, instruction=f"({keys})", **io)
    return add_hotkeys(question, q["multi"], exits, state, log).unsafe_ask()


def ask(q: dict, n: int, total: int, settings: dict, log: Log, **io) -> tuple[int, int]:
    print(f"\nВопрос {n}/{total} · {q['level']}" + (f" · {q['difficulty']}" if q.get("difficulty") else ""))
    log.q = q.get("id", str(n))
    n_hints = len(hints_of(q, settings))
    log.emit("question_shown", n=n, level=q["level"], difficulty=q.get("difficulty"), multi=q["multi"],
             hint_available=n_hints > 0, n_hints=n_hints)
    state, hints_shown = State(), 0
    while True:
        answer = prompt(q, hints_shown, settings, state, log, **io)
        if answer is SHOW_HINT:
            hints_shown += 1
            log.emit("hint_shown", level=hints_shown, of=n_hints, ms_since_question=state.ms())
        elif answer is PAUSE:
            log.emit("pause")
            p0 = time.monotonic()
            questionary.press_any_key_to_continue("⏸ Пауза — любая клавиша, чтобы продолжить", **io).unsafe_ask()
            paused = int((time.monotonic() - p0) * 1000)
            state.paused_ms += paused
            log.paused_ms += paused
            log.emit("resume", paused_ms=paused)
        else:
            break
    picked = answer if q["multi"] else [answer]
    got, best = score(q, picked)
    log.emit("answer", picked=sorted(picked), correct=[i for i, o in enumerate(q["options"]) if o["correct"]],
             got=got, max=best, ms_since_question=state.ms(), paused_ms=state.paused_ms, hints_used=hints_shown,
             n_toggles=state.toggles)
    right = "; ".join(o["text"] for o in q["options"] if o["correct"])
    print(f"{'✅' if got == best else '❌'} {got}/{best}. Верно: {right}")
    if q.get("explanation"):
        print(f"Разбор: {q['explanation']}")
    return got, best


def main() -> None:
    quiz_dir = Path(sys.argv[1])
    quiz_file = quiz_dir / "quiz.yaml"
    data = yaml.safe_load(quiz_file.read_text(encoding="utf-8"))
    questions = [q for q in data["questions"] if q.get("section", "main") == "main"]
    settings, log_cfg = load_settings(quiz_dir)
    print(data.get("title", ""))
    meta = data.get("meta") or {}
    if meta:
        print(f"Для кого: {meta['audience']}\nЦель: {meta['goal']}" + (f"\nВремя: ~{meta['duration_min']} мин" if meta.get("duration_min") else ""))
    who = identity(log_cfg)
    slug = re.sub(r"[^\w.-]+", "_", who["user"]) or "user"
    log_dir = quiz_dir / log_cfg["dir"]  # relative to the quiz dir
    log = Log(log_dir / f"{datetime.now():%y%m%d-%H%M%S}-{quiz_dir.resolve().name}-{slug}.jsonl")
    log.emit("run_start", **who, quiz_file=str(quiz_file), cwd=os.getcwd(), repo_commit=git("rev-parse", "--short", "HEAD"),
             python=platform.python_version(), platform=platform.platform(), n_questions=len(questions), meta=meta)
    got = best = 0
    try:
        for n, q in enumerate(questions, 1):
            g, b = ask(q, n, len(questions), settings, log)
            got, best = got + g, best + b
        end = "run_end"
    except (KeyboardInterrupt, EOFError):
        print("\nПрервано.")
        end = "interrupted"
    log.q = None
    log.emit(end, got=got, max=best, ms_total=int((time.monotonic() - log.t0) * 1000), paused_ms=log.paused_ms)
    print(f"\nИтог: {got} из {best}\nЛог: {log.path.resolve()}")


# self-check of the scoring rule
_m = {"multi": True, "options": [{"correct": c} for c in (True, True, False, True)]}
assert score(_m, [0, 1, 3]) == (3, 3) and score(_m, [0, 2]) == (0, 3) and score(_m, [2]) == (0, 3)
assert score({"multi": False, "options": [{"correct": False}, {"correct": True}]}, [1]) == (1, 1)

if __name__ == "__main__":
    main()
