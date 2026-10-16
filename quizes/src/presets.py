"""Presets: how one run of a quiz is assembled (mode, language, which questions, in which order).

quizes/src/presets.yaml (base) merged with <quiz_dir>/presets.yaml (optional); every key is required after the merge.
`select` is a pure function of (questions, preset, rng), so a run is reproducible from its seed.
"""
from pathlib import Path

import yaml

from settings import merge

BASE = Path(__file__).with_name("presets.yaml")
KEYS = ("description", "mode", "lang", "sections", "pick", "count", "difficulty_min", "difficulty_max", "order",
        "topics", "topic_order", "shuffle_options", "hints", "seed")
MODES = ("immediate", "exam")
ORDERS = ("as_is", "asc", "desc", "random")


def load_presets(quiz_dir: Path) -> dict[str, dict]:
    own = Path(quiz_dir) / "presets.yaml"
    merged = yaml.safe_load(BASE.read_text(encoding="utf-8"))["presets"]
    if own.exists():
        merged = merge(merged, (yaml.safe_load(own.read_text(encoding="utf-8")) or {}).get("presets") or {})
    return merged


def topic_names(q: dict) -> set[str]:
    """Topic of a (bilingual) question in every language."""
    t = q.get("topic")
    return {v for v in t.values() if v} if isinstance(t, dict) else ({t} if t else set())


def validate(name: str, p: dict, quiz_cfg: dict, langs: list[str], topics: set[str]) -> None:
    """Strict check of one preset; the error names the preset and the key."""
    def bad(key: str, why: str):
        raise ValueError(f"preset {name!r}: {key}: {why}")
    missing = [k for k in KEYS if k not in p]
    if missing:
        raise ValueError(f"preset {name!r}: keys not set: {', '.join(missing)} (see {BASE})")
    extra = [k for k in p if k not in KEYS]
    if extra:
        raise ValueError(f"preset {name!r}: unknown keys: {', '.join(extra)} (allowed: {', '.join(KEYS)})")
    diffs = quiz_cfg["difficulties"]
    if p["mode"] not in MODES:
        bad("mode", f"one of {', '.join(MODES)}")
    if p["lang"] != "ask" and p["lang"] not in langs:
        bad("lang", f"ask or one of {', '.join(langs)}")
    if not p["sections"] or not set(p["sections"]) <= {"main", "reserve"}:
        bad("sections", "a non-empty list of main / reserve")
    if p["pick"] not in ("first", "random"):
        bad("pick", "first or random")
    if p["count"] != "all" and not (isinstance(p["count"], int) and not isinstance(p["count"], bool) and p["count"] >= 1):
        bad("count", "all or a number >= 1")
    for k in ("difficulty_min", "difficulty_max"):
        if p[k] not in diffs:
            bad(k, f"one of {', '.join(diffs)}")
    if diffs.index(p["difficulty_min"]) > diffs.index(p["difficulty_max"]):
        bad("difficulty_min", "must not be harder than difficulty_max")
    if p["order"] not in ORDERS:
        bad("order", f"one of {', '.join(ORDERS)}")
    if p["topic_order"] not in ("mixed", "grouped"):
        bad("topic_order", "mixed or grouped")
    if p["topics"] != "all":
        if not isinstance(p["topics"], list) or not p["topics"]:
            bad("topics", "all or a non-empty list")
        unknown = [t for t in p["topics"] if t not in topics]
        if unknown:
            bad("topics", f"unknown {unknown}; the quiz has: {sorted(topics)}")
    for k in ("shuffle_options", "hints"):
        if not isinstance(p[k], bool):
            bad(k, "true or false")
    if p["seed"] is not None and (not isinstance(p["seed"], int) or isinstance(p["seed"], bool)):
        bad("seed", "a number or null")


def select(questions: list[dict], p: dict, quiz_cfg: dict, rng) -> list[dict]:
    """The questions of one run, in asking order. Steps: filter → pick count → order → group by topic → shuffle options."""
    diffs = quiz_cfg["difficulties"]
    lo, hi = diffs.index(p["difficulty_min"]), diffs.index(p["difficulty_max"])

    def rank(q):
        return diffs.index(q["difficulty"]) if q.get("difficulty") else None

    qs = [q for q in questions
          if q["section"] in p["sections"]
          and (rank(q) is None or lo <= rank(q) <= hi)
          and (p["topics"] == "all" or topic_names(q) & set(p["topics"]))]
    if not qs:
        raise ValueError("this preset selects no questions (check sections, difficulty range and topics)")
    n = len(qs) if p["count"] == "all" else min(p["count"], len(qs))
    if n < len(qs):
        if p["pick"] == "random":
            keep = set(rng.sample(range(len(qs)), n))
            qs = [q for i, q in enumerate(qs) if i in keep]
        else:
            qs = qs[:n]
    if p["order"] == "random":
        rng.shuffle(qs)
    elif p["order"] in ("asc", "desc"):
        qs = sorted(qs, key=lambda q: rank(q) or 0, reverse=p["order"] == "desc")
    if p["topic_order"] == "grouped":
        firsts: list = []
        for q in qs:
            key = sorted(topic_names(q))[:1]
            if key not in firsts:
                firsts.append(key)
        qs = sorted(qs, key=lambda q: firsts.index(sorted(topic_names(q))[:1]))
    if p["shuffle_options"]:
        shuffled = []
        for q in qs:
            idx = list(range(len(q["options"])))
            rng.shuffle(idx)
            shuffled.append({**q, "options": [{**q["options"][i], "orig": i} for i in idx]})
        qs = shuffled
    return qs
