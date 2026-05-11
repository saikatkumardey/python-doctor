"""State cache for score deltas across runs.

Persists per-category scores to ``<path>/.python-doctor/state.json`` so the
next run can show how the score moved.
"""

import json
import os
from datetime import datetime, timezone

from . import __version__
from .rules import AnalyzerResult
from .scorer import category_score

STATE_DIR = ".python-doctor"
STATE_FILE = "state.json"


def _state_path(path: str) -> str:
    return os.path.join(path, STATE_DIR, STATE_FILE)


def load_state(path: str) -> dict | None:
    """Read state.json from <path>/.python-doctor/. Return None if missing or corrupt."""
    state_path = _state_path(path)
    if not os.path.isfile(state_path):
        return None
    try:
        with open(state_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def save_state(path: str, results: list[AnalyzerResult], score: int) -> None:
    """Write per-category scores + total + timestamp + version to state.json."""
    categories = {r.category: category_score(r) for r in results}
    payload = {
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": score,
        "categories": categories,
    }
    state_dir = os.path.join(path, STATE_DIR)
    os.makedirs(state_dir, exist_ok=True)
    state_path = _state_path(path)
    with open(state_path, "w") as f:
        json.dump(payload, f, indent=2)


def compute_delta(prev: dict | None, current_results: list[AnalyzerResult], current_score: int) -> dict:
    """Compute score delta vs previous run.

    Returns a dict with keys:
      - total_delta: int
      - category_deltas: dict[str, int]
      - top_regression: (category, delta) | None  (most-negative drop, or None)
      - has_previous: bool
    """
    current_categories = {r.category: category_score(r) for r in current_results}

    if prev is None or not isinstance(prev.get("categories"), dict):
        return {
            "total_delta": 0,
            "category_deltas": {cat: 0 for cat in current_categories},
            "top_regression": None,
            "has_previous": False,
        }

    prev_score = prev.get("score", 0)
    prev_categories = prev["categories"]
    total_delta = current_score - prev_score

    category_deltas: dict[str, int] = {}
    for cat, cur in current_categories.items():
        prev_val = prev_categories.get(cat, cur)
        category_deltas[cat] = cur - prev_val

    regressions = [(cat, d) for cat, d in category_deltas.items() if d < 0]
    top_regression = min(regressions, key=lambda kv: kv[1]) if regressions else None

    return {
        "total_delta": total_delta,
        "category_deltas": category_deltas,
        "top_regression": top_regression,
        "has_previous": True,
    }
