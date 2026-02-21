"""Tests for the scorer module."""

from python_doctor.rules import AnalyzerResult
from python_doctor.scorer import category_score, compute_score, score_label


def test_compute_score_no_deductions():
    """Perfect score when no deductions."""
    results = [AnalyzerResult(category="security", deduction=0)]
    assert compute_score(results) == 100


def test_compute_score_with_deductions():
    """Score decreases with deductions."""
    results = [
        AnalyzerResult(category="security", deduction=10),
        AnalyzerResult(category="lint", deduction=5),
    ]
    assert compute_score(results) == 85


def test_compute_score_floor_at_zero():
    """Score cannot go below zero."""
    results = [AnalyzerResult(category="security", deduction=150)]
    assert compute_score(results) == 0


def test_score_label_excellent():
    assert score_label(95) == "Excellent"


def test_score_label_good():
    assert score_label(80) == "Good"


def test_score_label_needs_work():
    assert score_label(60) == "Needs Work"


def test_score_label_critical():
    assert score_label(30) == "Critical"


def test_category_score():
    """Category score is max_deduction minus actual deduction."""
    result = AnalyzerResult(category="security", deduction=12)
    assert category_score(result) == 18  # 30 - 12


def test_category_score_zero_deduction():
    result = AnalyzerResult(category="lint", deduction=0)
    assert category_score(result) == 25  # max for lint
