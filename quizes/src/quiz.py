"""Interactive terminal quiz from quizes/<name>.yaml (made by md2yaml.py), with a JSONL event log per run.

Usage: uv run --with questionary --with pyyaml python quizes/src/quiz.py quizes/quiz-4-dagster [--lang ru|en]
The language is asked at start when the quiz has several (quiz.<lang>.md) and --lang is not given.
Only the main section is asked; reserve questions are skipped.
Modes (quiz.mode): immediate — explanation and a ChatGPT/Claude prompt after every answer; exam — nothing until the end,
then a results table, explanations and prompts for the failed questions. Prompts are also saved next to the log.
Keys: digits 1–9 pick (single) or toggle (multi) an option, Enter answers, the hint key shows the hint,
the pause key pauses the timer (settings: quizes/src/settings.yml + <quiz_dir>/settings.yml).
Log: <quiz_dir>/<log.dir>/<yymmdd-HHMMSS>-<quiz>-<user>.jsonl — who/where at start, then every move, (un)choice, hint, pause, answer.
"""
import argparse
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
MODES = ("immediate", "exam")


def load_settings(quiz_dir: Path) -> tuple[dict, dict, dict]:
    """(quiz, log, lang) sections of the merged settings; missing keys or bad values raise ValueError."""
    cfg = load_merged(quiz_dir)
    require(cfg, *(f"quiz.{k}" for k in ("difficulties", "hint_difficulties", "hint_position", "hint_key", "pause_key",
                                           "mode", "hints_enabled")),
            *(f"log.{k}" for k in ("dir", "identity", "identity_env")), "lang")
    for code, L in cfg["lang"].items():
        require(cfg, *(f"lang.{code}.{k}" for k in ("difficulties", "ui", "prompt_failed")))
    quiz, log = cfg["quiz"], cfg["log"]
    if quiz["hint_position"] not in ("before", "after"):
        raise ValueError(f"{cfg['_files']}: quiz.hint_position must be before or after")
    if quiz["mode"] not in MODES:
        raise ValueError(f"{cfg['_files']}: quiz.mode must be one of {', '.join(MODES)}")
    if log["identity"] not in IDENTITY_MODES:
        raise ValueError(f"{cfg['_files']}: log.identity must be one of {', '.join(IDENTITY_MODES)}")
    return quiz, log, cfg["lang"]


def localize(data: dict, lang: str, quiz: dict, L: dict) -> dict:
    """Flat single-language copy of a bilingual quiz.yaml: every {ru, en} field becomes its `lang` value."""
    def pick(v):
        return v[lang] if isinstance(v, dict) and lang in v else v
    out = {**data, "title": pick(data["title"]), "meta": pick(data.get("meta") or {}), "questions": []}
    for q in data["questions"]:
        d = q.get("difficulty")
        out["questions"].append({
            **q, "level": pick(q["level"]), "topic": pick(q.get("topic")), "text": pick(q["text"]),
            "hints": pick(q.get("hints")) or [], "explanation": pick(q.get("explanation")),
            "difficulty_name": L["difficulties"][quiz["difficulties"].index(d)] if d else None,
            "options": [{**o, "text": pick(o["text"])} for o in q["options"]],
        })
    return out


def tr(settings: dict, name: str, /, **kw) -> str:
    """Interface string `name` of the chosen language (settings["ui"], from lang.<code>.ui)."""
    return settings["ui"][name].format(**kw)


class Log:
    """Append-only JSONL: one event per line, flushed at once so an interrupted run keeps everything."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.f, self.t0 = path, open(path, "a", encoding="utf-8"), time.monotonic()
        self.q: str | None = None
        self.paused_ms = 0

    def write_prompt(self, n: int, text: str) -> Path:
        """Append the prompt of a failed question to <log>-prompts.md (next to the JSONL log)."""
        path = self.path.with_name(self.path.stem + "-prompts.md")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"## {n} ({self.q})\n\n```text\n{text.rstrip()}\n```\n\n")
        return path

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


def identity(log_cfg: dict, ui: dict | None = None, **io) -> dict:
    """Who takes the quiz; log.identity picks how the user name is obtained."""
    who = {"identity_mode": log_cfg["identity"], "os_user": getpass.getuser(), "host": socket.gethostname(),
           "git_name": git("config", "user.name"), "git_email": git("config", "user.email")}
    if log_cfg["identity"] == "ask":
        ui = ui or {"ask_name": "Name:", "name_required": "Enter a name"}
        who["user"] = questionary.text(ui["ask_name"], validate=lambda s: bool(s.strip()) or ui["name_required"],
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
    ok = settings["hints_enabled"] and q.get("difficulty") in settings["hint_difficulties"]
    return (q.get("hints") or []) if ok else []


def prompt(q: dict, hints_shown: int, settings: dict, state: State, log: Log, **io) -> object:
    hints = hints_of(q, settings)
    bullets = "\n".join(tr(settings, "hint_n", i=i, n=len(hints), text=h) if len(hints) > 1 else tr(settings, "hint", text=h)
                        for i, h in enumerate(hints[:hints_shown], 1))
    message = q["text"]
    if bullets:
        if settings["hint_position"] == "before":
            print(bullets)
        else:
            message = f"{message}\n{bullets}"
    keys = [tr(settings, "keys_toggle" if q["multi"] else "keys_pick"), tr(settings, "keys_answer")]
    exits = {settings["pause_key"]: PAUSE}
    if hints_shown < len(hints):
        keys.append(tr(settings, "keys_hint_n", key=settings["hint_key"], i=hints_shown + 1, n=len(hints)) if len(hints) > 1
                    else tr(settings, "keys_hint", key=settings["hint_key"]))
        exits[settings["hint_key"]] = SHOW_HINT
    keys.append(tr(settings, "keys_pause", key=settings["pause_key"]))
    keys = ", ".join(keys)
    choices = [questionary.Choice(f"{i + 1}) {o['text']}", value=i) for i, o in enumerate(q["options"])]
    factory = questionary.checkbox if q["multi"] else questionary.select
    question = factory(message, choices=choices, instruction=f"({keys})", **io)
    return add_hotkeys(question, q["multi"], exits, state, log).unsafe_ask()


def build_prompt(q: dict, picked: list[int], settings: dict) -> str:
    """Copy-paste prompt for ChatGPT/Claude about a question answered not fully right (template: lang.<code>.prompt_failed)."""
    meta = settings.get("meta") or {}
    opts = q["options"]
    return settings["prompt_failed"].format(
        title=settings.get("title", ""), audience=meta.get("audience", ""), goal=meta.get("goal", ""),
        topic=q.get("topic") or "-", question=q["text"],
        options="\n".join(f"{i + 1}) {o['text']}" for i, o in enumerate(opts)),
        picked="; ".join(f"{i + 1}) {opts[i]['text']}" for i in sorted(picked)) or "-",
        correct="; ".join(f"{i + 1}) {o['text']}" for i, o in enumerate(opts) if o["correct"]),
        hints=" / ".join(q.get("hints") or []) or "-", explanation=q.get("explanation") or "-").rstrip()


def feedback(q: dict, got: int, best: int, settings: dict, prompt_text: str | None) -> None:
    """Verdict, explanation and (for a failed question) the prompt, as printed after an answer or in the exam report."""
    right = "; ".join(o["text"] for o in q["options"] if o["correct"])
    print(f"{'✅' if got == best else '❌'} {got}/{best}. {tr(settings, 'right', right=right)}")
    if q.get("explanation"):
        print(tr(settings, "explanation", text=q["explanation"]))
    if prompt_text:
        print("\n" + tr(settings, "prompt_header") + "\n" + "-" * 60 + "\n" + prompt_text + "\n" + "-" * 60)


def ask(q: dict, n: int, total: int, settings: dict, log: Log, results: list | None = None, **io) -> tuple[int, int]:
    shown_level = q["level"] + (f" · {q.get('difficulty_name') or q['difficulty']}" if q.get("difficulty") else "")
    print("\n" + tr(settings, "question", n=n, total=total, level=shown_level))
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
            questionary.press_any_key_to_continue(tr(settings, "pause"), **io).unsafe_ask()
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
             n_toggles=state.toggles, mode=settings["mode"])
    prompt_text = None
    if got < best:
        prompt_text = build_prompt(q, picked, settings)
        path = log.write_prompt(n, prompt_text)
        log.emit("prompt_generated", file=path.name, chars=len(prompt_text))
    if settings["mode"] == "immediate":
        feedback(q, got, best, settings, prompt_text)
    else:
        print(tr(settings, "accepted"))
    if results is not None:
        results.append({"n": n, "q": q, "got": got, "best": best, "prompt": prompt_text})
    return got, best


def exam_report(results: list[dict], settings: dict) -> None:
    """Exam mode: table of all answers, then explanation + prompt for every question not fully right."""
    if not results:
        return
    print("\n" + tr(settings, "report_title"))
    for r in results:
        mark = "✅" if r["got"] == r["best"] else "❌"
        print(tr(settings, "report_row", n=r["n"], mark=mark, got=r["got"], best=r["best"], topic=r["q"].get("topic") or ""))
    wrong = [r for r in results if r["got"] < r["best"]]
    if wrong:
        print("\n" + tr(settings, "report_wrong"))
    for r in wrong:
        print("\n" + tr(settings, "report_question", n=r["n"], text=r["q"]["text"]))
        feedback(r["q"], r["got"], r["best"], settings, r["prompt"])


def choose_language(langs: list[str], wanted: str | None, lang_cfg: dict, **io) -> str:
    if wanted:
        if wanted not in langs:
            sys.exit(f"--lang {wanted}: this quiz has only {', '.join(langs)}")
        return wanted
    if len(langs) == 1:
        return langs[0]
    return questionary.select(lang_cfg[langs[0]]["ui"]["language"], choices=langs, **io).unsafe_ask()


def main() -> None:
    ap = argparse.ArgumentParser(description="Interactive quiz")
    ap.add_argument("quiz_dir", type=Path)
    ap.add_argument("--lang")
    args = ap.parse_args()
    quiz_dir, quiz_file = args.quiz_dir, args.quiz_dir / "quiz.yaml"
    raw = yaml.safe_load(quiz_file.read_text(encoding="utf-8"))
    quiz_cfg, log_cfg, lang_cfg = load_settings(quiz_dir)
    lang = choose_language(raw["langs"], args.lang, lang_cfg)
    data = localize(raw, lang, quiz_cfg, lang_cfg[lang])
    settings = {**quiz_cfg, "lang": lang, "ui": lang_cfg[lang]["ui"], "prompt_failed": lang_cfg[lang]["prompt_failed"],
                "title": data.get("title", ""), "meta": data["meta"]}
    questions = [q for q in data["questions"] if q.get("section", "main") == "main"]
    print(data.get("title", ""))
    meta = data["meta"]
    if meta:
        print(tr(settings, "for_whom", text=meta["audience"]) + "\n" + tr(settings, "goal", text=meta["goal"])
              + (("\n" + tr(settings, "duration", n=meta["duration_min"])) if meta.get("duration_min") else ""))
    who = identity(log_cfg, settings["ui"])
    slug = re.sub(r"[^\w.-]+", "_", who["user"]) or "user"
    log_dir = quiz_dir / log_cfg["dir"]  # relative to the quiz dir
    log = Log(log_dir / f"{datetime.now():%y%m%d-%H%M%S}-{quiz_dir.resolve().name}-{slug}.jsonl")
    log.emit("run_start", **who, quiz_file=str(quiz_file), lang=lang, cwd=os.getcwd(),
             repo_commit=git("rev-parse", "--short", "HEAD"), python=platform.python_version(),
             platform=platform.platform(), n_questions=len(questions), mode=settings["mode"], meta=meta)
    got = best = 0
    results: list[dict] = []
    try:
        for n, q in enumerate(questions, 1):
            g, b = ask(q, n, len(questions), settings, log, results)
            got, best = got + g, best + b
        end = "run_end"
    except (KeyboardInterrupt, EOFError):
        print("\n" + tr(settings, "interrupted"))
        end = "interrupted"
    log.q = None
    if settings["mode"] == "exam":
        exam_report(results, settings)
    log.emit(end, got=got, max=best, ms_total=int((time.monotonic() - log.t0) * 1000), paused_ms=log.paused_ms,
             n_failed=sum(r["got"] < r["best"] for r in results))
    print("\n" + tr(settings, "total", got=got, best=best) + "\n" + tr(settings, "log", path=log.path.resolve()))
    prompts = log.path.with_name(log.path.stem + "-prompts.md")
    if prompts.exists():
        print(tr(settings, "prompts", path=prompts.resolve()))


# self-check of the scoring rule
_m = {"multi": True, "options": [{"correct": c} for c in (True, True, False, True)]}
assert score(_m, [0, 1, 3]) == (3, 3) and score(_m, [0, 2]) == (0, 3) and score(_m, [2]) == (0, 3)
assert score({"multi": False, "options": [{"correct": False}, {"correct": True}]}, [1]) == (1, 1)

if __name__ == "__main__":
    main()
