"""Quiz settings: quizes/src/settings.yml (base) deep-merged with <quiz_dir>/settings.yml (overrides)."""
from pathlib import Path

import yaml

BASE = Path(__file__).with_name("settings.yml")


def merge(base: dict, over: dict) -> dict:
    """Deep merge: dicts merge key by key, anything else in `over` replaces the base value."""
    out = dict(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_settings(quiz_dir: Path) -> dict:
    own = Path(quiz_dir) / "settings.yml"
    if not own.exists():
        raise ValueError(f"{own} missing (create it, even empty: overrides of {BASE})")
    cfg = merge(yaml.safe_load(BASE.read_text(encoding="utf-8")) or {},
                yaml.safe_load(own.read_text(encoding="utf-8")) or {})
    cfg["_files"] = f"{BASE} + {own}"
    return cfg


def require(cfg: dict, *paths: str) -> None:
    """Every dotted path (e.g. "quiz.hint_key") must exist; the error names all missing ones and both files."""
    missing = []
    for p in paths:
        node = cfg
        for part in p.split("."):
            if not isinstance(node, dict) or part not in node:
                missing.append(p)
                break
            node = node[part]
    if missing:
        raise ValueError(f"{cfg['_files']}: {', '.join(missing)} not set")
