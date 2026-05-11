"""Tests for the state cache and delta computation."""

from python_doctor.rules import AnalyzerResult
from python_doctor.scorer import compute_score
from python_doctor.state import compute_delta, load_state, save_state


def _make_results(scores: dict[str, float]):
    """Build AnalyzerResults from {category: target_category_score} mapping.

    Target score = max_deduction - deduction, so we invert to get deduction.
    """
    from python_doctor.rules import CATEGORIES
    out = []
    for cat, target in scores.items():
        ded = CATEGORIES[cat]["max_deduction"] - target
        out.append(AnalyzerResult(category=cat, deduction=ded))
    return out


def test_load_state_missing_file(tmp_path):
    """load_state returns None when file is absent."""
    assert load_state(str(tmp_path)) is None


def test_load_state_corrupt_json(tmp_path):
    """load_state returns None when file has invalid JSON."""
    state_dir = tmp_path / ".python-doctor"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("{not valid json")
    assert load_state(str(tmp_path)) is None


def test_load_state_non_dict_payload(tmp_path):
    """load_state returns None if payload is JSON but not an object."""
    state_dir = tmp_path / ".python-doctor"
    state_dir.mkdir()
    (state_dir / "state.json").write_text("[1, 2, 3]")
    assert load_state(str(tmp_path)) is None


def test_save_then_load_roundtrip(tmp_path):
    """save_state followed by load_state returns the same data."""
    results = _make_results({"security": 25, "lint": 16, "complexity": 15})
    score = compute_score(results)
    save_state(str(tmp_path), results, score)

    loaded = load_state(str(tmp_path))
    assert loaded is not None
    assert loaded["score"] == score
    assert loaded["categories"]["security"] == 25
    assert loaded["categories"]["lint"] == 16
    assert loaded["categories"]["complexity"] == 15
    assert "version" in loaded
    assert "timestamp" in loaded

    # Verify file actually lives at the expected location.
    expected = tmp_path / ".python-doctor" / "state.json"
    assert expected.is_file()


def test_compute_delta_no_previous():
    """compute_delta with prev=None gives has_previous=False and zero deltas."""
    results = _make_results({"security": 25, "lint": 20})
    score = compute_score(results)
    delta = compute_delta(None, results, score)

    assert delta["has_previous"] is False
    assert delta["total_delta"] == 0
    assert delta["top_regression"] is None
    assert delta["category_deltas"]["security"] == 0
    assert delta["category_deltas"]["lint"] == 0


def test_compute_delta_with_previous_positive():
    """compute_delta returns correct per-category and total deltas (improvement)."""
    prev = {
        "version": "test",
        "timestamp": "2026-05-10T00:00:00Z",
        "score": 80,
        "categories": {"security": 20, "lint": 15, "complexity": 15},
    }
    results = _make_results({"security": 25, "lint": 16, "complexity": 15})
    score = compute_score(results)
    delta = compute_delta(prev, results, score)

    assert delta["has_previous"] is True
    assert delta["total_delta"] == score - 80
    assert delta["category_deltas"]["security"] == 5
    assert delta["category_deltas"]["lint"] == 1
    assert delta["category_deltas"]["complexity"] == 0
    # No regressions, so top_regression should be None.
    assert delta["top_regression"] is None


def test_compute_delta_identifies_top_regression():
    """compute_delta picks the worst-dropping category."""
    prev = {
        "version": "test",
        "timestamp": "2026-05-10T00:00:00Z",
        "score": 90,
        "categories": {"security": 25, "lint": 20, "complexity": 15},
    }
    # security drops by 10, lint drops by 3, complexity unchanged.
    results = _make_results({"security": 15, "lint": 17, "complexity": 15})
    score = compute_score(results)
    delta = compute_delta(prev, results, score)

    assert delta["has_previous"] is True
    assert delta["category_deltas"]["security"] == -10
    assert delta["category_deltas"]["lint"] == -3
    assert delta["category_deltas"]["complexity"] == 0
    assert delta["top_regression"] == ("security", -10)


def test_compute_delta_missing_category_in_prev():
    """Categories absent from previous state default to current value (zero delta)."""
    prev = {
        "version": "test",
        "timestamp": "2026-05-10T00:00:00Z",
        "score": 50,
        "categories": {"security": 25},  # lint missing
    }
    results = _make_results({"security": 25, "lint": 18})
    score = compute_score(results)
    delta = compute_delta(prev, results, score)

    assert delta["has_previous"] is True
    assert delta["category_deltas"]["security"] == 0
    # lint absent from prev -> treated as no change.
    assert delta["category_deltas"]["lint"] == 0
