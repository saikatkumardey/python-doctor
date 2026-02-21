"""Tests for the rules module."""

from python_doctor.rules import CATEGORIES, AnalyzerResult, Finding


def test_finding_defaults():
    """Finding has sensible defaults."""
    f = Finding(category="security", rule="test", message="msg")
    assert f.file == ""
    assert f.line == 0
    assert f.severity == "medium"
    assert f.cost == 0.0


def test_analyzer_result_defaults():
    """AnalyzerResult has empty findings by default."""
    r = AnalyzerResult(category="lint")
    assert r.findings == []
    assert r.deduction == 0.0
    assert r.error is None


def test_all_categories_have_required_keys():
    """Every category must have emoji, label, and max_deduction."""
    for name, cat in CATEGORIES.items():
        assert "emoji" in cat, f"{name} missing emoji"
        assert "label" in cat, f"{name} missing label"
        assert "max_deduction" in cat, f"{name} missing max_deduction"
        assert isinstance(cat["max_deduction"], int)
